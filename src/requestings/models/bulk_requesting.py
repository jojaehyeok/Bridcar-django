from django.db import models

from users.models import Dealer

from pcar.helpers import PreprocessUploadPath


def file_path_getter(obj):
    return f'bulk-requestings'


class BulkRequesting(models.Model):
    client = models.ForeignKey(
        Dealer,
        on_delete=models.CASCADE,
        related_name='bulk_requestings',
        verbose_name='대상 딜러',
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='올린 시각',
    )

    file = models.FileField(
        upload_to=PreprocessUploadPath(file_path_getter, use_uuid_name=True),
        verbose_name='다량 발주 파일'
    )

    is_processed = models.BooleanField(
        default=False,
        verbose_name='처리여부',
    )

    class Meta:
        db_table = 'bulk_requestings'
        verbose_name = '다량 발주 신청 내역'
        verbose_name_plural = '다량 발주 신청 내역 목록'
