import json
import requests
import threading


class DaangnRequestingWebhookSender(threading.Thread):
    def __init__(self, hook_url='', requesting_id=None, reason='', **extra):
        super(DaangnRequestingWebhookSender, self).__init__()

        self.hook_url = hook_url
        self.requesting_id = requesting_id
        self.reason = reason
        self.extra = extra

    def run(self):
        if not self.hook_url or not self.requesting_id:
            return

        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
        }

        data = {
            'requesting_id': self.requesting_id,
            **self.extra,
        }

        if self.reason:
            data['reason'] = self.reason

        try:
            requests.post(
                self.hook_url,
                data=json.dumps(data),
                headers=headers,
            )
        except:
            pass
