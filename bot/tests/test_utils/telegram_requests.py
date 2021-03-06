from typing import Optional


class MockedUpdateRequest:
    def __init__(self, msg: Optional[dict] = None):
        self._json = msg

    @property
    def json(self):
        if not self._json:
            self._json = tg_updates_request_channel_channel()
        return self._json


def tg_updates_request_channel_channel():
    return {
        "update_id": 814547192,
        "message": {
            "message_id": 2,
            "from": {
                "id": 90422868,
                "is_bot": False,
                "first_name": "John",
                "last_name": "Smith",
                "username": "Js66"
            },
            "chat": {
                "id": -1001526646040,
                "title": "Test Chat",
                "type": "supergroup"
            },
            "date": 1629639673,
            "new_chat_participant": {
                "id": 218246197,
                "is_bot": True,
                "first_name": "Jyyeee",
                "username": "RDB"
            },
            "new_chat_member": {
                "id": 211246197,
                "is_bot": True,
                "first_name": "Jyyeee",
                "username": "RDB"
            },
            "new_chat_members": [
                {
                    "id": 211246197,
                    "is_bot": True,
                    "first_name": "Jyyeee",
                    "username": "RDB"
                }
            ]
        }
    }


def tg_updates_request_channel_dm():
    return {
        "update_id": 814933544,
        "message": {
            "message_id": 884238,
            "from": {
                "id": 90425568,
                "is_bot": False,
                "first_name": "John",
                "last_name": "Doe",
                "username": "jdoe",
                "language_code": "en"
            },
            "chat": {
                "id": 90425568,
                "first_name": "John",
                "last_name": "Doe",
                "username": "jdoe",
                "type": "private"
            },
            "date": 1276067696,
            "text": "replace me when needed"
        }
    }
