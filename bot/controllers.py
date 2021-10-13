import os

import ujson
from sanic import json, HTTPResponse
from sanic.log import logger

from bot.senders import send_msg, forward_msg

proxy_to = int(os.environ.get('PROXY_TO'))


async def health(request):
    return json({
        'api': True,
        'updates_callback': True if request.app.ctx.tg_webhook else False,
        'db': None
    })


async def send_to_user(txt: str):
    """
    txt must be in the form of:
    send || 90422868 || some message
    where:
    send - command to route the message to this coroutine
    90422868 - the chat_id to which to send the message
    some message - the message to be sent by the bot
    """
    cmd = [e.strip() for e in txt.split('||')]
    checks = (len(cmd) == 3, cmd[0] == 'send', cmd[1].isnumeric())
    if not all(checks):
        await send_msg(chat_id=proxy_to, msg=(f'Incorrect message received: {txt}. Expecting something in the form:'
                                              f' send || <chat_id> || <your_message_here'))
        return
    await send_msg(chat_id=int(cmd[1]), msg=cmd[2])


async def updates(request):
    try:
        message = request.json['message']
    except KeyError:  # we currently don't handle message edits, new chat members, kick notifications etc.
        logger.error(f'An update we don\'t handle received from Telegram: {request.json}')
        return HTTPResponse()
    if message['from']['is_bot']:
        return HTTPResponse()  # dismiss bots

    user_id = message['from']['id']
    chat_id = message['chat']['id']
    txt = message.get('text')

    if chat_id == proxy_to:
        if 'send' in txt:
            await send_to_user(txt)
        else:  # don't reply to replies to own messages on the PROXY_TO chat
            return HTTPResponse()
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
