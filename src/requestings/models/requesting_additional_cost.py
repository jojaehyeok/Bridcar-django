from django.db import models

from pcar.helpers import PreprocessUploadPath

from requestings.models import RequestingHistory
from requestings.constants import ADDITIONAL_COST_WORKING_TYPES, ADDITIONAL_COST_TYPES


def template_file_getter(obj):
    return f'external-evaluation-templates'


class RequestingAdditionalCost(models.Model):
    type = models.CharField(
        max_length=32,
        choices=ADDITIONAL_COST_TYPES,
        default='기타',
        verbose_name='요금 구분',
    )

    requesting_history = models.ForeignKey(
        RequestingHistory,
        on_delete=models.CASCADE,
        related_name='additional_costs',
        verbose_name='대상 의뢰',
    )

    name = models.CharField(
        max_length=100,
        verbose_name='추가 비용 내용',
    )

    cost = models.IntegerField(
        verbose_name='추가 비용'
    )

    working_type = models.CharField(
        max_length=50,
        choices=ADDITIONAL_COST_WORKING_TYPES,
        null=True,
        blank=True,
        verbose_name='추가 비용 발생 작업 구분',
    )

    image = models.ImageField(
        upload_to=PreprocessUploadPath(template_file_getter, use_uuid_name=True),
        null=True,
        blank=True,
        verbose_name='추가비용 증빙 이미지',
    )

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'requesting_additional_costs'
        verbose_name = '추가 요금'
        verbose_name_plural = '추가 요금 목록'
