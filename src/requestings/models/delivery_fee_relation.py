from django.db import models

from requestings.models import DeliveryRegionDivision


class DeliveryFeeRelation(models.Model):
    departure_region_division = models.ForeignKey(
        DeliveryRegionDivision,
        on_delete=models.CASCADE,
        related_name='fee_relation_as_departure',
        verbose_name='출발지 지역',
    )

    arrival_region_division = models.ForeignKey(
        DeliveryRegionDivision,
        on_delete=models.CASCADE,
        related_name='fee_relation_as_arrival',
        verbose_name='도착지 지역',
    )

    delivery_fee = models.PositiveIntegerField(
        default=0,
        verbose_name='탁송 요금',
    )

    class Meta:
        db_table = 'delivery_fee_relations'
        verbose_name = '탁송 요금 지역 관계'
        verbose_name_plural = '탁송 요금 지역 관계 목록'
