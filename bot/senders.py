from typing import Union

import httpx
from sanic.log import logger

from bot.configs import bot_url


async def send_command(url: str, data: dict) -> None:
    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=data)
        if not response.json()['ok']:
            logger.error(f'Unsuccessful request: {response.content}')
    return


async def send_msg(chat_id: int, msg: str, reply_to: int = None):
    url = await bot_url() + 'sendMessage'
    data = {
        'chat_id': chat_id,
        'text': msg,
    }
    if reply_to:
        data['reply_to_message_id'] = reply_to
    await send_command(url, data)


async def forward_msg(chat_id: Union[str, int], from_chat_id: Union[str, int], message_id: int):
    url = await bot_url() + 'forwardMessage'
    data = {
        'chat_id': chat_id,
        'from_chat_id': from_chat_id,
        'message_id': message_id
    }
    await send_command(url, data)