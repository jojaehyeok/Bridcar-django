from django.db import models

from users.models import Agent, BalanceHistory

from locations.models import CommonLocation

from requestings.constants import REQUESTING_TYPES

from .requesting_history import RequestingHistory


class RefererSettlement(models.Model):
    id = models.AutoField(primary_key=True, verbose_name='정산 번호')

    requesting_end_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='정산 시각'
    )

    user = models.ForeignKey(
        Agent,
        on_delete=models.CASCADE,
        related_name='referer_settlements',
        verbose_name='정산 대상 평카인',
    )

    requesting_history = models.ForeignKey(
        RequestingHistory,
        on_delete=models.CASCADE,
        related_name='referer_settlement',
        verbose_name='대상 의뢰',
    )

    revenue = models.PositiveIntegerField(
        default=0,
        verbose_name='홍보비 수익 금액',
    )

    tax = models.PositiveIntegerField(
        default=0,
        verbose_name='홍보비 수수료',
    )

    class Meta:
        db_table = 'referer_settlements'
        verbose_name = '홍보비 정산'
        verbose_name_plural = '홍보비 정산 목록'

    def save(self, *args, **kwargs):
        is_updating = self.pk != None

        super(RefererSettlement, self).save(*args, **kwargs)

        if not is_updating:
            BalanceHistory.objects.create(
                user=self.user,
                type='referer_revenue',
                amount=self.revenue,
            )
