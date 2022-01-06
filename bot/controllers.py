import os
from datetime import datetime

import aiosqlite
import ujson
from sanic import json, HTTPResponse, Request
from sanic.log import logger

from bot.caching import CACHE
from bot.senders import send_msg, forward_msg

proxy_to = int(os.environ.get('PROXY_TO'))


async def health(request: Request) -> json:
    return json({
        'api': True,
        'telegram_callback': True if request.app.ctx.tg_webhook else False,
        'db': os.path.isfile('bot/db.sql'),
        'caching': CACHE.get('synced')
    })


async def send_to_user(txt: str) -> None:
    """
    txt must be in the form of:
    send | 90422868 | some message
    where:
    send - command to route the message to this coroutine
    90422868 - the chat_id to which to send the message
    some message - the message to be sent by the bot
    """
    cmd = [e.strip() for e in txt.split('|')]
    if (not len(cmd) == 3) or (not cmd[0].lower() == 'send') or (not cmd[1].isnumeric()):
        await send_msg(chat_id=proxy_to, msg=(f'Incorrect message received: "{txt}". Expecting something in the form:'
                                              f' send | <chat_id> | <your_message_here>'))
        return
    await send_msg(chat_id=int(cmd[1]), msg=cmd[2])


async def ban_user(txt: str) -> None:
    cmd = [e.strip() for e in txt.split('|')]
    if (not len(cmd) == 2) or (not cmd[0].lower() == 'ban') or (not cmd[1].isnumeric()):
        await send_msg(chat_id=proxy_to, msg=(f'Incorrect message received: "{txt}". Expecting something in the form:'
                                              f' ban | <user id>'))
        return
    user_id = int(cmd[1])
    async with aiosqlite.connect('bot/db.sql') as db:
        await db.execute(
            "INSERT OR IGNORE INTO bans (tg_id, ban_timestamp) VALUES (?, ?);",
            (user_id, int(datetime.now().timestamp()))
        )
        await db.commit()
    CACHE['ban_list'].append(user_id)
    await send_msg(chat_id=proxy_to, msg=f'User {user_id} is now banned.')


async def unban_user(txt: str) -> None:
    cmd = [e.strip() for e in txt.split('|')]
    if (not len(cmd) == 2) or (not cmd[0].lower() == 'unban') or (not cmd[1].isnumeric()):
        await send_msg(chat_id=proxy_to, msg=(f'Incorrect message received: "{txt}". Expecting something in the form:'
                                              f' unban | <user id>'))
        return
    user_id = int(cmd[1])
    async with aiosqlite.connect('bot/db.sql') as db:
        async with db.execute("DELETE FROM bans WHERE tg_id=?;", (user_id, )) as cursor:
            row_count = cursor.rowcount
            await db.commit()
            found = True if row_count > 0 else False
    if not found:
        await send_msg(chat_id=proxy_to, msg=f'User {user_id} not found in the banned users list.')
        return
    try:
        CACHE['ban_list'].remove(user_id)
    except ValueError:
        logger.error(f'Cache out of sync with DB, could not find tg_id {user_id}. Restart the service to do a sync.')
    await send_msg(chat_id=proxy_to, msg=f'User {user_id} is now unbanned.')


async def show_bans() -> None:
    if CACHE['synced']:
        ban_list = CACHE['ban_list']
    else:
        ban_list = []
        async with aiosqlite.connect('bot/db.sql') as db:
            async with db.execute("SELECT tg_id FROM bans") as cursor:
                async for row in cursor:
                    ban_list.append(row[0])
        CACHE['ban_list'] = ban_list
        CACHE['synced'] = True
    await send_msg(chat_id=proxy_to, msg=f'Banned users: {ban_list}')


async def updates(request: Request) -> HTTPResponse:
    try:
        message = request.json['message']
    except KeyError:  # we currently don't handle message edits, new chat members, kick notifications etc.
        logger.error(f'An update we don\'t handle received from Telegram: {request.json}')
        return HTTPResponse()
    if message['from']['is_bot']:
        return HTTPResponse()  # dismiss bots

    user_id = message['from']['id']

    # ignore banned user
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

    # handle commands coming from the PROXY_TO chat id
    if chat_id == proxy_to and txt:
        if txt.lower().startswith('send'):
            await send_to_user(txt)
        elif txt.lower().startswith('ban'):
            await ban_user(txt)
        elif txt.lower().startswith('unban'):
            await unban_user(txt)
        elif txt.lower().startswith('showbans'):
            await show_bans()
        else:  # don't reply to replies to own messages in the PROXY_TO chat
            return HTTPResponse()

    # handle messages coming from regular users
    elif txt == '/myid':
        msg = f'Your ID: {user_id}. Chat ID: {chat_id}'
        await send_msg(chat_id=user_id, msg=msg, reply_to=message['message_id'])
    elif txt == '/start':
        start_reply = os.environ.get('START_REPLY')
        if start_reply:
            await send_msg(chat_id=user_id, msg=start_reply, reply_to=message['message_id'])
    else:
        await send_msg(chat_id=proxy_to, msg=f"Incoming message from: {ujson.dumps(message['from'])}")
        await forward_msg(chat_id=proxy_to, from_chat_id=chat_id, message_id=message['message_id'])

    return HTTPResponse(status=201)
