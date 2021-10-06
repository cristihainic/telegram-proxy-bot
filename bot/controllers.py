import os

from sanic import json, HTTPResponse

from bot.senders import send_msg, forward_msg


async def health(request):
    return json({
        'api': True,
        'updates_callback': True if request.app.ctx.tg_webhook else False,
        'db': None
    })


async def updates(request):
    try:
        message = request.json['message']
    except KeyError:
        return HTTPResponse(status=400)
    if message['from']['is_bot']:
        return json({}, status=201)  # dismiss bots

    user_id = message['from']['id']
    chat_id = message['chat']['id']

    if message.get('text') == '/myid':
        msg = f'Your ID: {user_id}. Chat ID: {chat_id}'
        await send_msg(chat_id=user_id, msg=msg, reply_to=message['message_id'])
    elif message.get('text') == '/start':
        start_reply = os.environ.get('START_REPLY')
        if start_reply:
            await send_msg(chat_id=user_id, msg=start_reply, reply_to=message['message_id'])
    else:
        await forward_msg(chat_id=os.environ.get('PROXY_TO'), from_chat_id=chat_id, message_id=message['message_id'])
        await send_msg(chat_id=user_id, msg=start_reply, reply_to=message['message_id'])
    return json({}, status=201)
