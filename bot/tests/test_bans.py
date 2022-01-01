import os
from datetime import datetime

import aiosqlite

from bot.controllers import updates
from bot.tests.test_utils.telegram_requests import MockedUpdateRequest


async def test_ban_command_adds_user_to_db_and_cache(mocker):
    mocked_send = mocker.patch('bot.controllers.send_msg')
    request = MockedUpdateRequest()
    message = request.json['message']
    message['text'] = 'ban || 1234567890'
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


async def test_banned_user_ignored():
    pass


async def test_unban_command_removed_user_from_db_and_cache():
    pass


async def test_showbans_command_retries_all_from_db():
    pass


async def test_showbans_command_updates_cache():
    pass
