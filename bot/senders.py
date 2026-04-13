import json

import httpx
from sanic.log import logger

from bot.configs import bot_url


async def send_command(url: str, data: dict) -> None:
    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=data)
        if not response.json()['ok']:
            logger.error(f'Unsuccessful request: {response.content}')
    return


async def send_msg(chat_id: str | int, msg: str, reply_to: int | None = None,
                   reply_markup: dict | None = None):
    url = await bot_url() + 'sendMessage'
    data = {
        'chat_id': chat_id,
        'text': msg,
    }
    if reply_to:
        data['reply_to_message_id'] = reply_to
    if reply_markup:
        data['reply_markup'] = json.dumps(reply_markup)
    await send_command(url, data)


async def forward_msg(chat_id: str | int, from_chat_id: str | int, message_id: int):
    url = await bot_url() + 'forwardMessage'
    data = {
        'chat_id': chat_id,
        'from_chat_id': from_chat_id,
        'message_id': message_id
    }
    await send_command(url, data)


async def copy_msg(chat_id: str | int, from_chat_id: str | int, message_id: int):
    url = await bot_url() + 'copyMessage'
    data = {
        'chat_id': chat_id,
        'from_chat_id': from_chat_id,
        'message_id': message_id,
    }
    await send_command(url, data)


async def answer_callback_query(callback_query_id: str, text: str):
    url = await bot_url() + 'answerCallbackQuery'
    data = {
        'callback_query_id': callback_query_id,
        'text': text,
    }
    await send_command(url, data)


async def set_my_commands(commands: list[dict], scope: dict | None = None):
    url = await bot_url() + 'setMyCommands'
    data = {'commands': json.dumps(commands)}
    if scope:
        data['scope'] = json.dumps(scope)
    await send_command(url, data)
