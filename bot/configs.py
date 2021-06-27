import os
import urllib.parse

import aiofiles


async def api_key():
    async with aiofiles.open('/run/secrets/BOT_API_KEY', mode='r') as f:
        key = await f.read()
    return key


async def bot_url():
    key = await api_key()
    return os.environ.get('TG_BASE_URL').format(key)


async def webhook():
    callback_base = os.environ.get('CALLBACK_URL_BASE')
    if not callback_base.endswith('/'):
        callback_base += '/'
    return callback_base + urllib.parse.quote_plus(f'{await api_key()}')
