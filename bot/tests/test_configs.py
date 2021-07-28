import urllib.parse

from bot.configs import api_key, webhook


async def test_api_key():
    key = await api_key()
    assert isinstance(key, str), not key.isspace()


async def test_webhook_url():
    assert urllib.parse.quote_plus(await api_key()) in await webhook()
