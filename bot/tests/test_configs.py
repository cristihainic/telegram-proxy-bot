import os
import urllib.parse

from bot.configs import api_key, webhook


async def test_api_key():
    os.system('printf "123asd-mybotkey-blabla" > /run/secrets/BOT_API_KEY')
    key = await api_key()
    assert isinstance(key, str), not key.isspace()


async def test_webhook_url():
    assert urllib.parse.quote_plus(await api_key()) in await webhook()
