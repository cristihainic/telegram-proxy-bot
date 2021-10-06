import os

from bot.controllers import updates
from bot.tests.test_utils.telegram_requests import MockedUpdateRequest


async def test_start_message(mocker):
    mocked_send_msg = mocker.patch('bot.controllers.send_msg')
    request = MockedUpdateRequest()
    message = request.json['message']
    message['text'] = '/start'
    os.environ['START_REPLY'] = 'testy testy'

    resp = await updates(request)

    assert resp.status == 201
    mocked_send_msg.assert_called_once_with(
        chat_id=message['from']['id'], msg='testy testy', reply_to=message['message_id']
    )


async def test_reply_myid(mocker):
    mocked_send_msg = mocker.patch('bot.controllers.send_msg')
    request = MockedUpdateRequest()
    message = request.json['message']
    message['text'] = '/myid'

    resp = await updates(request)

    assert resp.status == 201
    msg = f'Your ID: {message["from"]["id"]}. Chat ID: {message["chat"]["id"]}'
    mocked_send_msg.assert_called_once_with(
        chat_id=message['from']['id'], msg=msg, reply_to=message['message_id']
    )
