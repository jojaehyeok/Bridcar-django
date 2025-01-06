from django.db.models import Q, F
from django.utils import timezone

from requestings.models import RequestingHistory

from notifications.models import Notification
from notifications.utils import KakaoAlimtalkSender


def logging(content):
    now = timezone.now()
    print(f'({ now }) { content }')


def notify_when_estimated_service_date_modifiable():
    now = timezone.now()

    estimated_service_date_modifiable_requestings = RequestingHistory.objects \
        .filter(
            Q(status='WAITING_DELIVERY_WORKING')& \
            Q(daangn_requesting_information__isnull=False)& \
            Q(daangn_requesting_information__is_paid=True)& \
            Q(reservation_date__isnull=False)& \
            Q(reservation_date__lte=(now + timezone.timedelta(hours=2)))& \
            Q(reservation_date__gte=now)
        ) \
        .exclude(Q(deliverer__isnull=True))

    for requesting_history in estimated_service_date_modifiable_requestings:
        Notification.create(
            'USER',
            'DAANGN_REQUESTING_CONFIRMED',
            user=requesting_history.deliverer,
            actor=None,
            requesting_history=requesting_history,
            data=requesting_history
        )

        KakaoAlimtalkSender(
            template_code='DAANGN_REQ_CONFIRMED',
            receivers=[ str(requesting_history.deliverer.mobile_number) ],
            parameters={
                'car_number': requesting_history.car.number,
            }
        ).start()

    logging(f'total { len(estimated_service_date_modifiable_requestings) } requesting_histories processed')
