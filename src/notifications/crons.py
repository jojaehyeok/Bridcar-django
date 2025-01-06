from django.db.models import Q
from django.utils import timezone

from requestings.models import RequestingHistory

from notifications.models import Notification

def logging(content):
    now = timezone.now()
    print(f'({ now }) { content }')


def reminding_created_requesting():
    reminding_requestings = RequestingHistory.objects \
        .filter(
            Q(status='WAITING_AGENT')| \
            (
                Q(is_delivery_transferred=False)& \
                Q(status='WAITING_DELIVERER')
            )
        )

    now = timezone.now()

    reminding_requestings = reminding_requestings.filter(
        Q(created_at__lt=(now - timezone.timedelta(minutes=30)))
    )

    for requesting_history in reminding_requestings:
        Notification.objects.create(
            type='CONTROL_ROOM',
            subject='REMINDING_CREATED_REQUESTING',
            requesting_history=requesting_history,
        )


def delete_old_created_reminding_notifications():
    now = timezone.now()

    old_created_reminding_notifications = Notification.objects.filter(
        Q(type='CONTROL_ROOM')& \
        Q(subject='REMINDING_CREATED_REQUESTING')& \
        Q(created_at__lt=(now - timezone.timedelta(days=1)))
    )

    old_created_reminding_notifications.delete()
