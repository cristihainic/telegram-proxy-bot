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

    # Forward comes first (content-first layout)
    mocked_fwd.assert_called_once_with(
        chat_id=proxy_to, from_chat_id=message['chat']['id'], message_id=message['message_id']
    )

    # Action bar with ID + inline keyboard follows
    mocked_send.assert_called_once()
    call = mocked_send.call_args
    assert call.kwargs['chat_id'] == proxy_to
    assert call.kwargs['msg'] == 'ID: 90422868'
    assert 'reply_markup' in call.kwargs
