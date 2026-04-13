import os
import time
from datetime import datetime

import aiosqlite
from bot.caching import CACHE
from bot.controllers import updates, REPLY_TIMEOUT_SEC
from bot.tests.test_utils.telegram_requests import (
    MockedUpdateRequest, MockedCallbackQueryRequest,
)

proxy_to = int(os.environ.get('PROXY_TO'))


async def test_action_bar_includes_buttons(mocker):
    mocked_send = mocker.patch('bot.controllers.send_msg')
    mocker.patch('bot.controllers.forward_msg')

    request = MockedUpdateRequest()
    message = request.json['message']
    message['text'] = 'Proxy me.'

    await updates(request)

    call = mocked_send.call_args
    assert call.kwargs['chat_id'] == proxy_to
    assert call.kwargs['msg'] == 'ID: 90422868'
    assert call.kwargs['reply_markup'] == {
        'inline_keyboard': [[
            {'text': 'Reply', 'callback_data': 'r:90422868'},
            {'text': 'Ban', 'callback_data': 'b:90422868'},
        ]]
    }


async def test_forward_sent_before_action_bar(mocker):
    """Content-first layout: forward first, action bar second."""
    manager = mocker.MagicMock()
    manager.attach_mock(mocker.patch('bot.controllers.forward_msg'), 'fwd')
    manager.attach_mock(mocker.patch('bot.controllers.send_msg'), 'send')

    request = MockedUpdateRequest()
    request.json['message']['text'] = 'Proxy me.'

    await updates(request)

    # First call should be forward_msg, second should be send_msg
    assert manager.mock_calls[0][0] == 'fwd'
    assert manager.mock_calls[1][0] == 'send'


async def test_sender_info_cached_for_button_callbacks(mocker):
    mocker.patch('bot.controllers.send_msg')
    mocker.patch('bot.controllers.forward_msg')

    request = MockedUpdateRequest()
    message = request.json['message']
    message['text'] = 'Proxy me.'

    await updates(request)

    assert CACHE['name_cache'][90422868] == message['from']


async def test_callback_reply_sets_target(mocker):
    mocked_answer = mocker.patch('bot.controllers.answer_callback_query')
    mocker.patch('bot.controllers.send_msg', return_value={'result': {'message_id': 42}})
    CACHE['name_cache'][90422868] = {
        'id': 90422868, 'first_name': 'John', 'last_name': 'Smith', 'username': 'Js66'
    }

    request = MockedCallbackQueryRequest(data='r:90422868', from_user_id=111, cq_id='cq1')
    resp = await updates(request)
    assert resp.status == 201

    entry = CACHE['reply_targets'][111]
    assert entry['target_id'] == 90422868
    assert entry['target_name'] == 'John Smith (@Js66)'
    assert entry['expires_at'] > time.time()
    assert entry['reminder_msg_id'] == 42
    mocked_answer.assert_called_once_with('cq1', 'Replying to John Smith (@Js66)')


async def test_callback_reply_sends_persistent_reminder(mocker):
    """Tapping Reply should send a persistent in-chat reminder message."""
    mocker.patch('bot.controllers.answer_callback_query')
    mocked_send = mocker.patch(
        'bot.controllers.send_msg', return_value={'result': {'message_id': 99}}
    )
    CACHE['name_cache'][90422868] = {
        'id': 90422868, 'first_name': 'John', 'last_name': 'Smith', 'username': 'Js66'
    }

    request = MockedCallbackQueryRequest(data='r:90422868', from_user_id=111)
    await updates(request)

    mocked_send.assert_called_once()
    call = mocked_send.call_args
    assert call.kwargs['chat_id'] == proxy_to
    assert 'Replying to John Smith (@Js66)' in call.kwargs['msg']
    assert '10 min' in call.kwargs['msg']


async def test_callback_reply_without_cached_name(mocker):
    mocked_answer = mocker.patch('bot.controllers.answer_callback_query')
    mocker.patch('bot.controllers.send_msg', return_value={'result': {'message_id': 1}})

    request = MockedCallbackQueryRequest(data='r:5555', from_user_id=111)
    await updates(request)

    entry = CACHE['reply_targets'][111]
    assert entry['target_name'] == 'user 5555'
    mocked_answer.assert_called_once()
    assert 'user 5555' in mocked_answer.call_args.args[1]


async def test_callback_ban_writes_name_to_db(mocker):
    mocker.patch('bot.controllers.answer_callback_query')
    CACHE['name_cache'][90422868] = {
        'id': 90422868, 'first_name': 'John', 'last_name': 'Smith', 'username': 'Js66'
    }

    request = MockedCallbackQueryRequest(data='b:90422868')
    await updates(request)

    async with aiosqlite.connect('bot/db.sql') as db:
        async with db.execute(
            'SELECT tg_id, first_name, last_name, username FROM bans WHERE tg_id=?;',
            (90422868,)
        ) as cursor:
            row = await cursor.fetchone()
    assert row == (90422868, 'John', 'Smith', 'Js66')
    assert 90422868 in CACHE['ban_list']


async def test_callback_ban_fallback_when_cache_empty(mocker):
    mocker.patch('bot.controllers.answer_callback_query')
    request = MockedCallbackQueryRequest(data='b:90422868')

    await updates(request)

    async with aiosqlite.connect('bot/db.sql') as db:
        async with db.execute(
            'SELECT first_name, last_name, username FROM bans WHERE tg_id=?;',
            (90422868,)
        ) as cursor:
            row = await cursor.fetchone()
    assert row == (None, None, None)


def _pending_target(target_id, target_name, reminder_msg_id=None, ttl=REPLY_TIMEOUT_SEC):
    return {
        'target_id': target_id,
        'target_name': target_name,
        'expires_at': time.time() + ttl,
        'reminder_msg_id': reminder_msg_id,
    }


async def test_operator_message_routes_when_pending(mocker):
    mocked_send = mocker.patch('bot.controllers.send_msg')
    mocked_copy = mocker.patch('bot.controllers.copy_msg')
    mocker.patch('bot.controllers.delete_msg')
    operator_id = 777
    target_id = 42
    CACHE['reply_targets'][operator_id] = _pending_target(target_id, 'John')

    request = MockedUpdateRequest()
    message = request.json['message']
    message['from']['id'] = operator_id
    message['chat']['id'] = proxy_to
    message['text'] = 'Hi John'
    message['message_id'] = 999

    resp = await updates(request)
    assert resp.status == 201
    mocked_copy.assert_called_once_with(
        chat_id=target_id, from_chat_id=proxy_to, message_id=999)
    mocked_send.assert_called_once_with(chat_id=proxy_to, msg='✓ Sent to John')
    assert operator_id not in CACHE['reply_targets']


async def test_operator_message_deletes_reminder_after_routing(mocker):
    """When a pending reply is routed, the persistent reminder message gets deleted."""
    mocker.patch('bot.controllers.send_msg')
    mocker.patch('bot.controllers.copy_msg')
    mocked_delete = mocker.patch('bot.controllers.delete_msg')
    operator_id = 777
    CACHE['reply_targets'][operator_id] = _pending_target(42, 'John', reminder_msg_id=1234)

    request = MockedUpdateRequest()
    message = request.json['message']
    message['from']['id'] = operator_id
    message['chat']['id'] = proxy_to
    message['text'] = 'Hi John'

    await updates(request)
    mocked_delete.assert_called_once_with(chat_id=proxy_to, message_id=1234)


async def test_operator_message_skips_delete_if_no_reminder(mocker):
    """If the reminder send failed (no message_id stored), delete shouldn't be called."""
    mocker.patch('bot.controllers.send_msg')
    mocker.patch('bot.controllers.copy_msg')
    mocked_delete = mocker.patch('bot.controllers.delete_msg')
    operator_id = 777
    CACHE['reply_targets'][operator_id] = _pending_target(42, 'John', reminder_msg_id=None)

    request = MockedUpdateRequest()
    message = request.json['message']
    message['from']['id'] = operator_id
    message['chat']['id'] = proxy_to
    message['text'] = 'Hi John'

    await updates(request)
    mocked_delete.assert_not_called()


async def test_operator_media_routes_when_pending(mocker):
    """Operator sends a photo (no text) with a pending reply target — should be copied."""
    mocker.patch('bot.controllers.send_msg')
    mocked_copy = mocker.patch('bot.controllers.copy_msg')
    mocker.patch('bot.controllers.delete_msg')
    operator_id = 777
    CACHE['reply_targets'][operator_id] = _pending_target(42, 'John')

    request = MockedUpdateRequest()
    message = request.json['message']
    message['from']['id'] = operator_id
    message['chat']['id'] = proxy_to
    message['message_id'] = 500
    # No 'text' key — simulates a photo-only message
    message.pop('text', None)
    message['photo'] = [{'file_id': 'abc', 'width': 100, 'height': 100}]

    await updates(request)
    mocked_copy.assert_called_once_with(
        chat_id=42, from_chat_id=proxy_to, message_id=500)


async def test_operator_message_ignored_when_no_pending(mocker):
    mocked_send = mocker.patch('bot.controllers.send_msg')
    mocked_copy = mocker.patch('bot.controllers.copy_msg')

    request = MockedUpdateRequest()
    message = request.json['message']
    message['chat']['id'] = proxy_to
    message['text'] = 'just chatting'

    resp = await updates(request)
    assert resp.status == 201
    mocked_send.assert_not_called()
    mocked_copy.assert_not_called()


async def test_pending_target_expires(mocker):
    mocked_send = mocker.patch('bot.controllers.send_msg')
    mocked_copy = mocker.patch('bot.controllers.copy_msg')
    mocker.patch('bot.controllers.delete_msg')
    operator_id = 777
    # expired 1 second ago
    CACHE['reply_targets'][operator_id] = _pending_target(42, 'John', ttl=-1)

    request = MockedUpdateRequest()
    message = request.json['message']
    message['from']['id'] = operator_id
    message['chat']['id'] = proxy_to
    message['text'] = 'too late'

    await updates(request)
    mocked_copy.assert_not_called()
    mocked_send.assert_not_called()
    assert operator_id not in CACHE['reply_targets']


async def test_legacy_send_command_no_longer_routes(mocker):
    mocked_send = mocker.patch('bot.controllers.send_msg')
    mocked_copy = mocker.patch('bot.controllers.copy_msg')

    request = MockedUpdateRequest()
    message = request.json['message']
    message['chat']['id'] = proxy_to
    message['text'] = 'send | 90422868 | some message'

    await updates(request)
    mocked_send.assert_not_called()
    mocked_copy.assert_not_called()


async def test_callback_invalid_data(mocker):
    mocked_answer = mocker.patch('bot.controllers.answer_callback_query')
    request = MockedCallbackQueryRequest(data='garbage')
    await updates(request)
    mocked_answer.assert_called_once_with('cq_test_1', 'Invalid button data.')


async def test_callback_unknown_action(mocker):
    mocked_answer = mocker.patch('bot.controllers.answer_callback_query')
    request = MockedCallbackQueryRequest(data='x:42')
    await updates(request)
    mocked_answer.assert_called_once_with('cq_test_1', 'Unknown action.')


async def test_ban_timestamp_recorded(mocker):
    mocker.patch('bot.controllers.answer_callback_query')
    request = MockedCallbackQueryRequest(data='b:55')
    start = int(datetime.now().timestamp())
    await updates(request)
    end = int(datetime.now().timestamp())
    async with aiosqlite.connect('bot/db.sql') as db:
        async with db.execute('SELECT ban_timestamp FROM bans WHERE tg_id=55;') as cursor:
            row = await cursor.fetchone()
    assert start <= row[0] <= end
