import os

from bot.controllers import updates
from bot.tests.test_utils.telegram_requests import MockedUpdateRequest, tg_updates_request_channel_dm

proxy_to = int(os.environ.get('PROXY_TO'))


async def test_proxy_to(mocker):
    mocked_send = mocker.patch('bot.controllers.send_msg')
    mocked_fwd = mocker.patch('bot.controllers.forward_msg')

    request = MockedUpdateRequest()
    message = request.json['message']
    message['text'] = 'This should be proxied.'

    resp = await updates(request)

    assert resp.status == 201

    msg = ('Incoming message from: {"id":90422868,"is_bot":false,"first_name":"John","last_name":"Smith",'
           '"username":"Js66"}')
    mocked_send.assert_called_once_with(chat_id=proxy_to, msg=msg)

    mocked_fwd.assert_called_once_with(
        chat_id=proxy_to, from_chat_id=message['chat']['id'], message_id=message['message_id']
    )


async def test_proxy_from_success(mocker):
    mocked_send = mocker.patch('bot.controllers.send_msg')

    msg = tg_updates_request_channel_dm()
    msg['message']['chat']['id'] = proxy_to
    msg['message']['text'] = 'send||90422868 || some message'
    request = MockedUpdateRequest(msg=msg)

    resp = await updates(request)

    assert resp.status == 201

    mocked_send.assert_called_once_with(chat_id=90422868, msg='some message')


async def test_proxy_from_failure(mocker):
    mocked_send = mocker.patch('bot.controllers.send_msg')

    msg = tg_updates_request_channel_dm()
    msg['message']['chat']['id'] = proxy_to
    msg['message']['text'] = 'send || text instead of id :0 || some message'
    request = MockedUpdateRequest(msg=msg)

    resp = await updates(request)
    assert resp.status == 201

    error_msg = ('Incorrect message received: send || text instead of id :0 || some message. '
                 'Expecting something in the form: send || <chat_id> || <your_message_here')

    mocked_send.assert_called_once_with(chat_id=proxy_to, msg=error_msg)
