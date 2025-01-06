import json
import requests
import threading

from typing import List, Dict, Optional

from django.conf import settings


class ChannelTalkGroupMessageSender(threading.Thread):
    def __init__(self, text_value: str):
        super(ChannelTalkGroupMessageSender, self).__init__()

        self.text_value = text_value

    def run(self):
        recipient_list = []

        headers = {
            'x-access-key': settings.CHANNEL_TALK_API_ACCESS_KEY,
            'x-access-secret': settings.CHANNEL_TALK_API_SECRET,
            'Content-Type': 'application/json;charset=UTF-8',
        }

        blocks = [
            {
                'type': 'text',
                'value': self.text_value,
            }
        ]

        data = {
            'blocks': blocks,
        }

        requests.post(
            settings.CHANNEL_TALK_API_ENDPOINT \
                + f'/open/v5/groups/{ settings.CHANNEL_TALK_GROUP_ID_FOR_NOTIFICATION }/messages',
            data=json.dumps(data),
            headers=headers,
        )
