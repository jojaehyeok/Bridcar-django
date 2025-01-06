from django.db import models

from pcar.helpers import PreprocessUploadPath

from requestings.models import RequestingHistory
from requestings.constants import REQUESTING_CHATTING_SENDING_TO

from users.models import User


def message_image_path_getter(obj):
    return f'requestings/{ obj.requesting_history.pk }/chatting-messages'


class RequestingChattingMessage(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='requesting_chatting_messages',
        verbose_name='작성한 유저',
    )

    requesting_history = models.ForeignKey(
        RequestingHistory,
        on_delete=models.CASCADE,
        related_name='chatting_messages',
        verbose_name='대상 의뢰',
    )

    created_at = models.DateTimeField(auto_now_add=True)

    text = models.CharField(
        max_length=300,
        null=True,
        blank=True,
        verbose_name='채팅 메시지',
    )

    sending_to = models.CharField(
        max_length=30,
        choices=REQUESTING_CHATTING_SENDING_TO,
    )

    image = models.ImageField(
        upload_to=PreprocessUploadPath(message_image_path_getter, use_uuid_name=True),
        null=True,
        blank=True,
        verbose_name='채팅 이미지',
    )

    read_users = models.ManyToManyField(
        User,
        related_name='read_requesting_messages',
        verbose_name='읽은 사람',
    )

    def __str__(self):
        return f'{ self.requesting_history.pk }번 의뢰 채팅 메시지'

    class Meta:
        db_table = 'requesting_chatting_messages'
        verbose_name = '의뢰 채팅 메시지'
        verbose_name_plural = '의뢰 채팅 메시지 목록'
