import io
import json
import base64
import requests

import xlsxwriter

from django.conf import settings


def request_toss_payments_virtual_account(order_id, amount, bank, user):
    basic_authorization_key = base64.b64encode(f'{ settings.TOSS_PAYMENTS_API_SECRET_KEY }:'.encode()) \
        .decode()

    headers = {
        'Authorization': f'Basic { basic_authorization_key }',
        'Content-Type': 'application/json',
    }

    response = requests.post(
        settings.TOSS_PAYMENTS_API_URL + '/v1/virtual-accounts',
        headers=headers,
        data=json.dumps({
            'orderId': str(order_id),
            'orderName': '평카인 가상계좌 입금',
            'amount': amount,
            'bank': bank,
            'customerName': user.name,
            'accountType': '고정',
            'accountKey': user.id,
            'virtualAccountCallbackUrl': settings.PUBLIC_URL + '/v1/users/balance-histories/deposits/results',
        })
    ).json()

    return response['secret'], response['virtualAccount']['accountNumber'], response['virtualAccount']['dueDate']

