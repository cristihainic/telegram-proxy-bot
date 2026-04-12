import os

from bot.controllers import updates
from bot.tests.test_utils.telegram_requests import MockedUpdateRequest

proxy_to = int(os.environ.get('PROXY_TO'))


async def test_proxy_to(mocker):
    mocked_send = mocker.patch('bot.controllers.send_msg')
    mocked_fwd = mocker.patch('bot.controllers.forward_msg')

    request = MockedUpdateRequest()
    message = request.json['message']
    message['text'] = 'This should be proxied.'

    resp = await updates(request)

    assert resp.status == 201

    # Pre-flight uses readable format + inline keyboard
    mocked_send.assert_called_once()
    call = mocked_send.call_args
    assert call.kwargs['chat_id'] == proxy_to
    assert call.kwargs['msg'] == 'From: John Smith (@Js66)\nID: 90422868'
    assert 'reply_markup' in call.kwargs

    mocked_fwd.assert_called_once_with(
        chat_id=proxy_to, from_chat_id=message['chat']['id'], message_id=message['message_id']
    )


async def test_proxy_to_without_preflight(mocker, monkeypatch):
    monkeypatch.setattr('bot.controllers.preflight', False)
    mocked_send = mocker.patch('bot.controllers.send_msg')
    mocked_fwd = mocker.patch('bot.controllers.forward_msg')

    request = MockedUpdateRequest()
    message = request.json['message']
    message['text'] = 'This should be proxied.'

    resp = await updates(request)

    assert resp.status == 201
    mocked_send.assert_not_called()
    mocked_fwd.assert_called_once_with(
        chat_id=proxy_to, from_chat_id=message['chat']['id'], message_id=message['message_id']
    )
