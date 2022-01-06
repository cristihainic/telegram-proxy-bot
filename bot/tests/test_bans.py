import os
from datetime import datetime

import aiosqlite
from bot.caching import CACHE

from bot.controllers import updates
from bot.tests.test_utils.telegram_requests import MockedUpdateRequest


async def test_ban_command_adds_user_to_db_and_cache(mocker):
    mocked_send = mocker.patch('bot.controllers.send_msg')
    request = MockedUpdateRequest()
    message = request.json['message']
    message['text'] = 'ban | 1234567890'
    message['chat']['id'] = int(os.environ.get('PROXY_TO'))

    resp = await updates(request)
    assert resp.status == 201
    mocked_send.assert_called_once_with(
        chat_id=int(os.environ.get('PROXY_TO')),
        msg='User 1234567890 is now banned.')

    action_start = int(datetime.now().timestamp())
    async with aiosqlite.connect('bot/db.sql') as db:
        async with db.execute('SELECT tg_id, ban_timestamp FROM bans LIMIT 1;') as cursor:
            async for row in cursor:
                tg_id, timestamp = row[0], row[1]
    assert tg_id == 1234567890
    assert action_start <= timestamp <= int(datetime.now().timestamp())
    assert tg_id in CACHE['ban_list']


async def test_banned_user_ignored(mocker):
    mocked_send = mocker.patch('bot.controllers.send_msg')
    mocked_fwd = mocker.patch('bot.controllers.forward_msg')
    request = MockedUpdateRequest()
    message = request.json['message']
    from_id = message['from']['id']

    async with aiosqlite.connect('bot/db.sql') as db:
        await db.execute(
            'INSERT INTO bans (tg_id, ban_timestamp) VALUES (?, ?)', (from_id, int(datetime.now().timestamp()))
        )
        await db.commit()

    resp = await updates(request)

    assert resp.status == 200

    mocked_send.assert_not_called()
    mocked_fwd.assert_not_called()


async def test_unban_command_removed_user_from_db_and_cache(mocker):
    async with aiosqlite.connect('bot/db.sql') as db:
        await db.execute(
            'INSERT INTO bans (tg_id, ban_timestamp) VALUES (?, ?)', (1234567890, int(datetime.now().timestamp()))
        )
        await db.commit()
    CACHE['ban_list'] = [1234567890]
    mocked_send = mocker.patch('bot.controllers.send_msg')
    request = MockedUpdateRequest()
    message = request.json['message']
    message['text'] = 'unban | 1234567890'
    message['chat']['id'] = int(os.environ.get('PROXY_TO'))

    resp = await updates(request)
    assert resp.status == 201
    mocked_send.assert_called_once_with(
        chat_id=int(os.environ.get('PROXY_TO')),
        msg='User 1234567890 is now unbanned.')

    async with aiosqlite.connect('bot/db.sql') as db:
        async with db.execute(
                "SELECT EXISTS(SELECT 1 FROM bans WHERE tg_id=?) LIMIT 1;", (1234567890,)) as cursor:
            assert (await cursor.fetchone())[0] == 0

    assert 1234567890 not in CACHE['ban_list']


async def test_showbans_command_retrieves_all_and_updates_cache(mocker):
    insert_tuples = [
        (123, int(datetime.now().timestamp())),
        (321, int(datetime.now().timestamp())),
        (231, int(datetime.now().timestamp()))
    ]
    async with aiosqlite.connect('bot/db.sql') as db:
        await db.executemany(
            'INSERT INTO bans (tg_id, ban_timestamp) VALUES (?, ?);', insert_tuples
        )
        await db.commit()

    mocked_send = mocker.patch('bot.controllers.send_msg')
    request = MockedUpdateRequest()
    message = request.json['message']
    message['text'] = 'showbans'
    message['chat']['id'] = int(os.environ.get('PROXY_TO'))

    resp = await updates(request)
    assert resp.status == 201

    mocked_send.assert_called_once_with(
        chat_id=int(os.environ.get('PROXY_TO')),
        msg='Banned users: [123, 231, 321]'
    )
    assert CACHE['ban_list'] == [123, 231, 321]
