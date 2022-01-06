import os

import aiosqlite
import pytest

from bot.sql import CREATE_BANS_TABLE


@pytest.fixture(autouse=True)
async def persistence_setup_and_teardown():
    async with aiosqlite.connect('bot/db.sql') as db:
        await db.execute(CREATE_BANS_TABLE)
        await db.commit()

    yield

    os.remove('bot/db.sql')
