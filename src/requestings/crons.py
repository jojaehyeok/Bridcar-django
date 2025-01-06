from pytz import timezone as pytz_timezone

from django.db.models import Q, F
from django.utils import timezone
from requestings.constants import REQUESTING_TYPES

from users.models import User

from requestings.models import RequestingHistory
from requestings.utils import handover_delivery

from notifications.utils import KakaoAlimtalkSender


def logging(content):
    now = timezone.now()
    print(f'({ now }) { content }')


def notify_starting_soon_requestings():
    now = timezone.now().astimezone(pytz_timezone('Asia/Seoul'))
    time_limit = now + timezone.timedelta(minutes=30)

    starting_soon_requestings = RequestingHistory.objects.filter(
        (
            Q(status='WAITING_WORKING')| \
            Q(status='WAITING_DELIVERY_WORKING')
        )& \
        Q(estimated_service_date__isnull=False)& \
        Q(estimated_service_date__date=time_limit.date())& \
        Q(estimated_service_date__hour=time_limit.hour)& \
        Q(estimated_service_date__minute=time_limit.minute)
    )

    for requesting_history in starting_soon_requestings:
        receiver = None

        if requesting_history.type == 'ONLY_DELIVERY':
            receiver = requesting_history.deliverer
        else:
            if requesting_history.status == 'WAITING_WORKING':
                receiver = requesting_history.agent
            elif requesting_history.status == 'WAITING_DELIVERY_WORKING':
                receiver = requesting_history.deliverer

        if receiver != None:
            if not receiver.is_test_account:
                KakaoAlimtalkSender(
                    template_code='START_WORKING_SOON',
                    receivers=[ str(receiver.mobile_number) ],
                    parameters={
                        'car_number': requesting_history.car.number,
                        'requesting_type': dict(REQUESTING_TYPES)[requesting_history.type],
                        'client_name': requesting_history.client.name,
                        'company_name': requesting_history.client.dealer_profile.company_name,
                        'source_address': f'{ requesting_history.source_location.road_address } { requesting_history.source_location.detail_address }',
                    }
                ).start()


def check_delayed_delivery_working():
    now = timezone.now()

    long_waiting_requestings = RequestingHistory.objects.filter(
        Q(status='WAITING_DELIVERY_WORKING')& \
        Q(deliverer=F('agent'))& \
        Q(delivery_proceed_decided_at__lte=(now - timezone.timedelta(minutes=5)))
    )

    for requesting in long_waiting_requestings:
        if ((now - requesting.delivery_proceed_decided_at).total_seconds() / 60) >= 2:
            handover_delivery(requesting)
