import os
from datetime import datetime, timezone

import aiosqlite
from bot.caching import CACHE

from bot.controllers import updates
from bot.tests.test_utils.telegram_requests import MockedUpdateRequest

proxy_to = int(os.environ.get('PROXY_TO'))


async def test_ban_cmd_adds_user_to_db_and_cache(mocker):
    mocked_send = mocker.patch('bot.controllers.send_msg')
    request = MockedUpdateRequest()
    message = request.json['message']
    message['text'] = '/ban 1234567890'
    message['chat']['id'] = proxy_to

    resp = await updates(request)
    assert resp.status == 201
    mocked_send.assert_called_once_with(
        chat_id=proxy_to, msg='user 1234567890 is now banned.')

    action_start = int(datetime.now().timestamp())
    async with aiosqlite.connect('bot/db.sql') as db:
        async with db.execute(
            'SELECT tg_id, ban_timestamp, first_name, last_name, username FROM bans LIMIT 1;'
        ) as cursor:
            row = await cursor.fetchone()
    tg_id, timestamp, first_name, last_name, username = row
    assert tg_id == 1234567890
    assert action_start <= timestamp <= int(datetime.now().timestamp())
    assert first_name is None and last_name is None and username is None
    assert tg_id in CACHE['ban_list']


async def test_ban_cmd_with_cached_name_writes_full_row(mocker):
    CACHE['name_cache'][1234567890] = {
        'id': 1234567890, 'first_name': 'Jane', 'last_name': 'Doe', 'username': 'jdoe'
    }
    mocked_send = mocker.patch('bot.controllers.send_msg')
    request = MockedUpdateRequest()
    message = request.json['message']
    message['text'] = '/ban 1234567890'
    message['chat']['id'] = proxy_to

    resp = await updates(request)
    assert resp.status == 201
    mocked_send.assert_called_once_with(
        chat_id=proxy_to, msg='Jane Doe (@jdoe) is now banned.')

    async with aiosqlite.connect('bot/db.sql') as db:
        async with db.execute(
            'SELECT first_name, last_name, username FROM bans WHERE tg_id=?;',
            (1234567890,)
        ) as cursor:
            row = await cursor.fetchone()
    assert row == ('Jane', 'Doe', 'jdoe')


async def test_ban_cmd_bad_input(mocker):
    mocked_send = mocker.patch('bot.controllers.send_msg')
    request = MockedUpdateRequest()
    message = request.json['message']
    message['text'] = '/ban notanumber'
    message['chat']['id'] = proxy_to

    resp = await updates(request)
    assert resp.status == 201
    mocked_send.assert_called_once_with(chat_id=proxy_to, msg='Usage: /ban <user_id>')

    async with aiosqlite.connect('bot/db.sql') as db:
        async with db.execute('SELECT COUNT(*) FROM bans;') as cursor:
            count = (await cursor.fetchone())[0]
    assert count == 0


async def test_banned_user_ignored(mocker):
    mocked_send = mocker.patch('bot.controllers.send_msg')
    mocked_fwd = mocker.patch('bot.controllers.forward_msg')
    request = MockedUpdateRequest()
    message = request.json['message']
    from_id = message['from']['id']

    async with aiosqlite.connect('bot/db.sql') as db:
        await db.execute(
            'INSERT INTO bans (tg_id, ban_timestamp) VALUES (?, ?)',
            (from_id, int(datetime.now().timestamp()))
        )
        await db.commit()

    resp = await updates(request)
    assert resp.status == 200
    mocked_send.assert_not_called()
    mocked_fwd.assert_not_called()


async def test_unban_cmd_removes_user(mocker):
    async with aiosqlite.connect('bot/db.sql') as db:
        await db.execute(
            'INSERT INTO bans (tg_id, ban_timestamp) VALUES (?, ?)',
            (1234567890, int(datetime.now().timestamp()))
        )
        await db.commit()
    CACHE['ban_list'] = [1234567890]
    mocked_send = mocker.patch('bot.controllers.send_msg')
    request = MockedUpdateRequest()
    message = request.json['message']
    message['text'] = '/unban 1234567890'
    message['chat']['id'] = proxy_to

    resp = await updates(request)
    assert resp.status == 201
    mocked_send.assert_called_once_with(
        chat_id=proxy_to, msg='User 1234567890 is now unbanned.')

    async with aiosqlite.connect('bot/db.sql') as db:
        async with db.execute(
                "SELECT EXISTS(SELECT 1 FROM bans WHERE tg_id=?) LIMIT 1;", (1234567890,)) as cursor:
            assert (await cursor.fetchone())[0] == 0
    assert 1234567890 not in CACHE['ban_list']


async def test_unban_cmd_bad_input(mocker):
    mocked_send = mocker.patch('bot.controllers.send_msg')
    request = MockedUpdateRequest()
    message = request.json['message']
    message['text'] = '/unban notanumber'
    message['chat']['id'] = proxy_to

    await updates(request)
    mocked_send.assert_called_once_with(chat_id=proxy_to, msg='Usage: /unban <user_id>')


async def test_unban_cmd_user_not_found(mocker):
    mocked_send = mocker.patch('bot.controllers.send_msg')
    request = MockedUpdateRequest()
    message = request.json['message']
    message['text'] = '/unban 9999'
    message['chat']['id'] = proxy_to

    await updates(request)
    mocked_send.assert_called_once_with(
        chat_id=proxy_to, msg='User 9999 not found in the banned users list.')


async def test_bans_cmd_empty(mocker):
    mocked_send = mocker.patch('bot.controllers.send_msg')
    request = MockedUpdateRequest()
    message = request.json['message']
    message['text'] = '/bans'
    message['chat']['id'] = proxy_to

    resp = await updates(request)
    assert resp.status == 201
    mocked_send.assert_called_once_with(chat_id=proxy_to, msg='No banned users.')


async def test_bans_cmd_formats_list(mocker):
    ts1 = int(datetime(2026, 4, 12, tzinfo=timezone.utc).timestamp())
    ts2 = int(datetime(2026, 4, 10, tzinfo=timezone.utc).timestamp())
    ts3 = int(datetime(2025, 8, 2, tzinfo=timezone.utc).timestamp())
    async with aiosqlite.connect('bot/db.sql') as db:
        await db.executemany(
            'INSERT INTO bans (tg_id, ban_timestamp, first_name, last_name, username) '
            'VALUES (?, ?, ?, ?, ?);',
            [
                (19612312371, ts1, 'John', 'Smith', 'JS666'),
                (98765, ts2, 'Jane', 'Doe', None),
                (11111, ts3, None, None, None),  # legacy row
            ]
        )
        await db.commit()

    mocked_send = mocker.patch('bot.controllers.send_msg')
    request = MockedUpdateRequest()
    message = request.json['message']
    message['text'] = '/bans'
    message['chat']['id'] = proxy_to

    await updates(request)
    expected = (
        'Banned users:\n'
        '• John Smith (@JS666) — ID 19612312371 — 2026-04-12\n'
        '• Jane Doe — ID 98765 — 2026-04-10\n'
        '• user 11111 — ID 11111 — 2025-08-02'
    )
    mocked_send.assert_called_once_with(chat_id=proxy_to, msg=expected)


async def test_legacy_pipe_ban_ignored(mocker):
    mocked_send = mocker.patch('bot.controllers.send_msg')
    request = MockedUpdateRequest()
    message = request.json['message']
    message['text'] = 'ban | 1234567890'
    message['chat']['id'] = proxy_to

    resp = await updates(request)
    assert resp.status == 201
    mocked_send.assert_not_called()

    async with aiosqlite.connect('bot/db.sql') as db:
        async with db.execute('SELECT COUNT(*) FROM bans;') as cursor:
            count = (await cursor.fetchone())[0]
    assert count == 0


async def test_bot_username_suffix_accepted(mocker):
    """In groups, Telegram can append @BotUsername to commands."""
    mocked_send = mocker.patch('bot.controllers.send_msg')
    request = MockedUpdateRequest()
    message = request.json['message']
    message['text'] = '/ban@MyTestBot 1234567890'
    message['chat']['id'] = proxy_to

    await updates(request)
    mocked_send.assert_called_once_with(chat_id=proxy_to, msg='user 1234567890 is now banned.')
