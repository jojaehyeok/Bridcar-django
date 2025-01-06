import json
import requests
import threading

from typing import List, Dict, Optional

from django.conf import settings

class KakaoAlimtalkSender(threading.Thread):
    def __init__(self, template_code: str, receivers: List[str], parameters: Optional[Dict[str, str]] = None):
        super(KakaoAlimtalkSender, self).__init__()

        self.template_code = template_code
        self.receivers = receivers
        self.parameters = parameters

    def run(self):
        recipient_list = []

        headers = {
            'X-Secret-Key': settings.NHN_CLOUD_ALIMTALK_SECRET_KEY,
            'Content-Type': 'application/json;charset=UTF-8',
        }

        for receiver in self.receivers:
            recipient = {
                'recipientNo': receiver.replace('-', ''),
                'templateParameter': self.parameters,
            }

            recipient_list.append(recipient)

        data = {
            'senderKey': settings.NHN_CLOUD_ALIMTALK_SENDER_KEY,
            'templateCode': self.template_code,
            'recipientList': recipient_list,
        }

        requests.post(
            settings.NHN_CLOUD_API_END_POINT \
                + f'/alimtalk/v2.2/appkeys/{ settings.NHN_CLOUD_ALIMTALK_APPKEY }/messages',
            data=json.dumps(data),
            headers=headers,
        ).json()
