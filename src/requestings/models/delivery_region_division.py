from django.db import models

from requestings.models import RequestingHistory


class DeliveryRegionDivision(models.Model):
    name = models.CharField(
        max_length=64,
        verbose_name='지역 이름',
    )

    address_name = models.TextField(
        verbose_name='소속 주소 (개행으로 구분)',
    )

    class Meta:
        db_table = 'delivery_region_divisions'
        verbose_name = '탁송 요금 산정용 지역 분할'
        verbose_name_plural = '탁송 요금 산정용 지역 분할 목록'

    def __str__(self):
        return self.name
