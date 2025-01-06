import json
import threading

from fcm_django.models import FCMDevice
from firebase_admin.messaging import APNSConfig, APNSPayload, AndroidConfig, Aps, Message, Notification

from requestings.models import RequestingHistory
from requestings.serializers import RequestingHistorySerializerForNotification

class FCMSender(threading.Thread):
    def __init__(
            self,
            device,
            subject,
            actor=None,
            requesting_history: RequestingHistory | None=None,
            body_message=None
    ):
        super(FCMSender, self).__init__()

        self.device = device
        self.notification_subject = subject
        self.actor = actor
        self.requesting_history = requesting_history
        self.body_message = body_message
        self.working_type_str = ''

        if requesting_history != None:
            if requesting_history.type == 'EVALUATION_DELIVERY':
                self.working_type_str = '진단평가'
            elif requesting_history.type == 'INSPECTION_DELIVERY':
                self.working_type_str = '검수'

    @property
    def notification_title(self):
        if self.notification_subject == 'CREATE_REQUESTING':
            return f'근처에 새로운 오더가 있습니다.'
        if self.notification_subject == 'START_EVALUATION':
            return f'{ self.requesting_history.car.number } 차량의 { self.working_type_str }를 시작합니다.'
        elif self.notification_subject == 'FINISH_EVALUATION':
            return f'{ self.requesting_history.car.number } 차량의 { self.working_type_str }를 완료했습니다.'
        elif self.notification_subject == 'CLIENT_CONFIRM_ARRIVAL_DELIVERY':
            return f'{ self.requesting_history.car.number } 차량의 매입유무가 결정되었습니다.'
        elif self.notification_subject == 'DEPARTURE_DELIVERY':
            return f'{ self.requesting_history.car.number } 차량의 탁송을 출발합니다.'
        elif self.notification_subject == 'ARRIVAL_DELIVERY':
            return f'{ self.requesting_history.car.number } 차량의 탁송이 완료되었습니다.'
        elif self.notification_subject == 'CLIENT_CONFIRM_ARRIVAL_DELIVERY':
            return f'{ self.requesting_history.car.number } 차량의 의뢰인이 탁송 인도를 확인했습니다.'
        elif self.notification_subject == 'REQUESTING_CHATTING':
            return f'{ self.requesting_history.car.number } 새로운 메시지'
        elif self.notification_subject == 'DAANGN_REQUESTING_CONFIRMED':
            return f'판매자가 준비 완료되었습니다.'

    @property
    def notification_body(self):
        if self.notification_subject == 'START_EVALUATION':
            return f'평가사가 차량을 꼼꼼하게 { self.working_type_str }하는동안 잠시만 기다려주세요!'
        elif self.notification_subject == 'FINISH_EVALUATION':
            return f'지금 바로 { self.working_type_str }결과를 앱에서 확인해보세요.'
        elif self.notification_subject == 'CLIENT_CONFIRM_ARRIVAL_DELIVERY':
            return f'앱에서 결과 확인 후 탁송관련 업무를 진행해주세요.'
        elif self.notification_subject == 'DEPARTURE_DELIVERY':
            return f'신청해주신 목적지까지 차량을 안전하게 탁송할게요.'
        elif self.notification_subject == 'ARRIVAL_DELIVERY':
            return f'앱에서 차량 인도 확인을해주세요!'
        elif self.notification_subject == 'REQUESTING_CHATTING':
            return self.body_message
        elif self.notification_subject == 'DAANGN_REQUESTING_CONFIRMED':
            return f'해당 의뢰의 예상 도착시각을 입력 후, 탁송을 진행해주세요!'


    @property
    def message_data(self):
        data = {
            'subject': self.notification_subject,
        }

        if self.requesting_history != None:
            data['requesting_history'] = json.dumps(
                RequestingHistorySerializerForNotification(self.requesting_history).data
            )

        return data

    def run(self):
        self.device.send_message(
            Message(
                notification=Notification(
                    title=self.notification_title,
                    body=self.notification_body,
                ),
                data=self.message_data,
                android=AndroidConfig(
                    priority='high',
                ),
                apns=APNSConfig(
                    payload=APNSPayload(
                        aps=Aps(
                            content_available=True,
                        )
                    )
                )
            )
        )
