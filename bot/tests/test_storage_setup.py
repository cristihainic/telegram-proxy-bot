import os.path

import aiosqlite

from bot.caching import CACHE
from bot.app import storage_setup


async def test_db_is_set_up():
    await storage_setup()

    assert os.path.isfile('bot/db.sql')
    async with aiosqlite.connect('bot/db.sql') as db:
        async with db.execute("SELECT name FROM sqlite_master WHERE type='table';") as cursor:
            result = await cursor.fetchone()
            assert result[0] == 'bans'


async def test_cache_is_synced_when_setting_up():
    existing_entries = (
        (123, 12345678),
        (234, 23456789),
        (345, 34567890)
    )
    async with aiosqlite.connect('bot/db.sql') as db:
        await db.executemany("INSERT INTO bans (tg_id, ban_timestamp) VALUES (?, ?);", existing_entries)
        await db.commit()

    await storage_setup()
    assert CACHE['synced']
    assert CACHE['ban_list'] == [123, 234, 345]


async def test_existing_data_persisted():
    """Calls storage_setup() multiple times"""
    async with aiosqlite.connect('bot/db.sql') as db:
        await db.execute("INSERT INTO bans (tg_id, ban_timestamp) VALUES (?, ?);", (123, 12345))
        await db.commit()

    await storage_setup()
    assert CACHE['ban_list'] == [123]

    async with aiosqlite.connect('bot/db.sql') as db:
        await db.executemany("INSERT INTO bans (tg_id, ban_timestamp) VALUES (?, ?);", ((234, 12345), (345, 12345)))
        await db.commit()
    await storage_setup()
    assert CACHE['ban_list'] == [123, 234, 345]

    await storage_setup()
    async with aiosqlite.connect('bot/db.sql') as db:
        async with db.execute("SELECT tg_id from bans;") as cursor:
            result = await cursor.fetchall()
            ids = []
            for r in result:
                ids.append(r[0])

    assert ids == [123, 234, 345]
