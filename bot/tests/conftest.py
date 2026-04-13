import os

import aiosqlite
import pytest

from bot.caching import CACHE
from bot.sql import CREATE_BANS_TABLE


@pytest.fixture(autouse=True)
async def persistence_setup_and_teardown():
    CACHE['synced'] = False
    CACHE['ban_list'] = []
    CACHE['reply_targets'] = {}
    CACHE['name_cache'] = {}

    async with aiosqlite.connect('bot/db.sql') as db:
        await db.execute(CREATE_BANS_TABLE)
        await db.commit()

    yield

    try:
        os.remove('bot/db.sql')
    except FileNotFoundError:
        pass
