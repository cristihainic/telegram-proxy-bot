# import os.path
#
# import aiosqlite
#
# from bot.app import storage_setup
#
#
# async def test_db_is_setup():
#     await storage_setup()
#     assert os.path.isfile('bot/db.sql')
#     # con = sqlite3.connect("data.db")
#     # cursor = con.cursor()
#     # cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
#
#
# async def test_cache_is_synced_when_setting_up():
#     pass
#
#
# async def test_existing_data_persisted():
#     pass
