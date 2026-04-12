import os
import time
from datetime import datetime, timezone

import aiosqlite
from sanic import json as sanic_json, HTTPResponse, Request
from sanic.log import logger

from bot.caching import CACHE
from bot.senders import send_msg, forward_msg, copy_msg, answer_callback_query

proxy_to = int(os.environ.get('PROXY_TO'))

REPLY_TIMEOUT_SEC = 600


async def health(request: Request) -> sanic_json:
    return sanic_json({
        'api': True,
        'telegram_callback': True if request.app.ctx.tg_webhook else False,
        'db': os.path.isfile('bot/db.sql'),
        'caching': CACHE.get('synced')
    })


def format_sender(user: dict) -> str:
    parts = [user.get('first_name') or '', user.get('last_name') or '']
    name = ' '.join(p for p in parts if p).strip()
    username = f" (@{user['username']})" if user.get('username') else ''
    display = f"{name}{username}".strip()
    return display or f"user {user.get('id', '?')}"


async def _do_ban(user_id: int, user_info: dict | None = None) -> None:
    first_name = user_info.get('first_name') if user_info else None
    last_name = user_info.get('last_name') if user_info else None
    username = user_info.get('username') if user_info else None
    async with aiosqlite.connect('bot/db.sql') as db:
        await db.execute(
            "INSERT OR IGNORE INTO bans (tg_id, ban_timestamp, first_name, last_name, username) "
            "VALUES (?, ?, ?, ?, ?);",
            (user_id, int(datetime.now().timestamp()), first_name, last_name, username)
        )
        await db.commit()
    if user_id not in CACHE['ban_list']:
        CACHE['ban_list'].append(user_id)


async def _do_unban(user_id: int) -> bool:
    async with aiosqlite.connect('bot/db.sql') as db:
        async with db.execute("DELETE FROM bans WHERE tg_id=?;", (user_id, )) as cursor:
            found = cursor.rowcount > 0
            await db.commit()
    if not found:
        return False
    try:
        CACHE['ban_list'].remove(user_id)
    except ValueError:
        logger.error(f'Cache out of sync with DB, could not find tg_id {user_id}. Restart the service to do a sync.')
    return True


async def ban_cmd(arg: str) -> None:
    arg = arg.strip()
    if not arg.isnumeric():
        await send_msg(chat_id=proxy_to, msg='Usage: /ban <user_id>')
        return
    user_id = int(arg)
    user_info = CACHE['name_cache'].get(user_id)
    await _do_ban(user_id=user_id, user_info=user_info)
    name = format_sender(user_info) if user_info else f'user {user_id}'
    await send_msg(chat_id=proxy_to, msg=f'{name} is now banned.')


async def unban_cmd(arg: str) -> None:
    arg = arg.strip()
    if not arg.isnumeric():
        await send_msg(chat_id=proxy_to, msg='Usage: /unban <user_id>')
        return
    user_id = int(arg)
    found = await _do_unban(user_id=user_id)
    if found:
        await send_msg(chat_id=proxy_to, msg=f'User {user_id} is now unbanned.')
    else:
        await send_msg(chat_id=proxy_to, msg=f'User {user_id} not found in the banned users list.')


async def list_bans() -> None:
    rows = []
    async with aiosqlite.connect('bot/db.sql') as db:
        async with db.execute(
            "SELECT tg_id, ban_timestamp, first_name, last_name, username FROM bans ORDER BY ban_timestamp DESC;"
        ) as cursor:
            async for row in cursor:
                rows.append(row)

    if not rows:
        await send_msg(chat_id=proxy_to, msg='No banned users.')
        return

    lines = ['Banned users:']
    for tg_id, ts, first_name, last_name, username in rows:
        name_parts = [p for p in (first_name, last_name) if p]
        name = ' '.join(name_parts)
        if username:
            name = f'{name} (@{username})'.strip() if name else f'@{username}'
        if not name:
            name = f'user {tg_id}'
        date = datetime.fromtimestamp(ts, tz=timezone.utc).strftime('%Y-%m-%d')
        lines.append(f'• {name} — ID {tg_id} — {date}')
    await send_msg(chat_id=proxy_to, msg='\n'.join(lines))


def _pop_reply_target(operator_id: int) -> tuple[int, str] | None:
    entry = CACHE['reply_targets'].pop(operator_id, None)
    if not entry:
        return None
    target_id, target_name, expires_at = entry
    if time.time() > expires_at:
        return None
    return target_id, target_name


async def handle_callback_query(cq: dict) -> HTTPResponse:
    operator_id = cq['from']['id']
    data = cq.get('data') or ''
    cq_id = cq['id']

    try:
        action, target_id_str = data.split(':', 1)
        target_id = int(target_id_str)
    except (ValueError, AttributeError):
        await answer_callback_query(cq_id, 'Invalid button data.')
        return HTTPResponse(status=201)

    target_info = CACHE['name_cache'].get(target_id)
    target_name = format_sender(target_info) if target_info else f'user {target_id}'

    if action == 'r':
        CACHE['reply_targets'][operator_id] = (
            target_id, target_name, time.time() + REPLY_TIMEOUT_SEC
        )
        await answer_callback_query(cq_id, f'Replying to {target_name}. Send your next message.')
    elif action == 'b':
        await _do_ban(user_id=target_id, user_info=target_info)
        await answer_callback_query(cq_id, f'{target_name} is now banned.')
    else:
        await answer_callback_query(cq_id, 'Unknown action.')
    return HTTPResponse(status=201)


async def updates(request: Request) -> HTTPResponse:
    # Button taps arrive as callback_query, not message.
    if 'callback_query' in request.json:
        return await handle_callback_query(request.json['callback_query'])

    try:
        message = request.json['message']
    except KeyError:  # edits, chat-member events, etc.
        logger.error(f'An update we don\'t handle received from Telegram: {request.json}')
        return HTTPResponse()
    if message['from']['is_bot']:
        return HTTPResponse()  # dismiss bots

    user_id = message['from']['id']

    # ignore banned users
    if CACHE['synced']:
        if user_id in CACHE['ban_list']:
            return HTTPResponse()
    else:
        async with aiosqlite.connect('bot/db.sql') as db:
            async with db.execute(
                    "SELECT EXISTS(SELECT 1 FROM bans WHERE tg_id=?) LIMIT 1;", (user_id, )) as cursor:
                if (await cursor.fetchone())[0] == 1:
                    return HTTPResponse()
    chat_id = message['chat']['id']
    txt = message.get('text')

    # Messages from the PROXY_TO chat: slash commands or pending-reply routing
    if chat_id == proxy_to:
        if txt and txt.startswith('/'):
            parts = txt.split(maxsplit=1)
            cmd = parts[0].lstrip('/').split('@')[0].lower()
            arg = parts[1] if len(parts) > 1 else ''
            if cmd == 'ban':
                await ban_cmd(arg)
                return HTTPResponse(status=201)
            if cmd == 'unban':
                await unban_cmd(arg)
                return HTTPResponse(status=201)
            if cmd == 'bans':
                await list_bans()
                return HTTPResponse(status=201)
            # Unknown slash command — fall through
        target = _pop_reply_target(user_id)
        if target:
            target_id, target_name = target
            await copy_msg(
                chat_id=target_id,
                from_chat_id=proxy_to,
                message_id=message['message_id'],
            )
            await send_msg(chat_id=proxy_to, msg=f'✓ Sent to {target_name}')
        # else: internal group discussion — ignore
        return HTTPResponse(status=201)

    # Regular-user commands
    if txt == '/myid':
        msg = f'Your ID: {user_id}. Chat ID: {chat_id}'
        await send_msg(chat_id=user_id, msg=msg, reply_to=message['message_id'])
    elif txt == '/start':
        start_reply = os.environ.get('START_REPLY')
        if start_reply:
            await send_msg(chat_id=user_id, msg=start_reply, reply_to=message['message_id'])
    else:
        CACHE['name_cache'][user_id] = message['from']
        await forward_msg(chat_id=proxy_to, from_chat_id=chat_id, message_id=message['message_id'])
        reply_markup = {
            'inline_keyboard': [[
                {'text': 'Reply', 'callback_data': f'r:{user_id}'},
                {'text': 'Ban', 'callback_data': f'b:{user_id}'},
            ]]
        }
        await send_msg(chat_id=proxy_to, msg=f'ID: {user_id}', reply_markup=reply_markup)

    return HTTPResponse(status=201)
