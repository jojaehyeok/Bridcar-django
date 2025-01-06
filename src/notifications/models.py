from typing import List

from django.db import models
from django.db.models.query import QuerySet

from multiselectfield import MultiSelectField

from fcm_django.models import FCMDevice

from users.models import User

from requestings.models import RequestingHistory

from notifications.utils import FCMSender
from notifications.constants import NOTIFICATION_SUBJECT, NOTIFICATION_TYPES


class Notification(models.Model):
    type = MultiSelectField(
        max_length=32,
        choices=NOTIFICATION_TYPES,
        verbose_name='알림 구분',
    )

    subject = models.CharField(
        max_length=32,
        choices=NOTIFICATION_SUBJECT,
        verbose_name='알림 주제',
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='알림 생성 시각',
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='유저',
        null=True,
        blank=True,
    )

    actor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='acting_notifications',
        verbose_name='행위자',
        null=True,
        blank=True,
    )

    requesting_history = models.ForeignKey(
        RequestingHistory,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='대상 의뢰',
        null=True,
        blank=True,
    )

    data = models.CharField(
        max_length=100,
        verbose_name='추가 데이터',
        null=True,
        blank=True,
    )

    is_read = models.BooleanField(
        default=False,
        verbose_name='알림 읽음 여부'
    )

    class Meta:
        db_table = 'notifications'
        verbose_name = '알림'
        verbose_name_plural = '알림 목록'

    @staticmethod
    def create(
        type: str | List[str],
        subject: str,
        user: List[User] | User | None=None,
        actor=None,
        requesting_history: RequestingHistory | None=None,
        data=None,
        body_message=None,
        send_fcm=True,
    ):
        if isinstance(user, list) or isinstance(user, QuerySet):
            Notification.objects.bulk_create(
                [
                    Notification(
                        type=type,
                        subject=subject,
                        user=user,
                        actor=actor,
                        requesting_history=requesting_history,
                        data=data,
                    ) for user in user
                ]
            )

            devices = FCMDevice.objects.filter(
                user__id__in=[ user.pk for user in user ],
                active=True,
            )

            if len(devices) > 0:
                sender = FCMSender(devices, subject, actor, requesting_history=requesting_history, body_message=body_message)
                sender.start()
        elif user is None:
            Notification.objects.create(
                type=type,
                subject=subject,
                user=user,
                actor=actor,
                requesting_history=requesting_history,
                data=data,
            )

            if send_fcm:
                devices = FCMDevice.objects.filter(active=True)

                if len(devices) > 0:
                    sender = FCMSender(devices, subject, actor, requesting_history=requesting_history, body_message=body_message)
                    sender.start()
        else:
            notification = Notification.objects.create(
                type=type,
                subject=subject,
                user=user,
                actor=actor,
                requesting_history=requesting_history,
                data=data,
            )

            if send_fcm:
                device = user.fcmdevice_set.filter(active=True).first()

                if device:
                    sender = FCMSender(device, subject, actor, requesting_history=requesting_history, body_message=body_message)
                    sender.start()

            return notification
