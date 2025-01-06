import math

from django.db import models
from django.db.models import Q, Sum

from users.models import Agent, BalanceHistory

from locations.models import CommonLocation

from requestings.constants import REQUESTING_TYPES

from .requesting_history import RequestingHistory
from .requesting_additional_cost import RequestingAdditionalCost


class RequestingSettlement(models.Model):
    id = models.AutoField(primary_key=True, verbose_name='정산번호')

    requesting_end_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='정산 시각'
    )

    user = models.ForeignKey(
        Agent,
        on_delete=models.CASCADE,
        related_name='settlements',
        verbose_name='정산 대상 평카인',
    )

    requesting_history = models.ForeignKey(
        RequestingHistory,
        on_delete=models.CASCADE,
        related_name='settlement',
        verbose_name='대상 의뢰',
    )

    evaluation_cost = models.PositiveIntegerField(
        default=0,
        verbose_name='평카 요금',
    )

    inspection_cost = models.PositiveIntegerField(
        default=0,
        verbose_name='검수 요금',
    )

    delivering_cost = models.PositiveIntegerField(
        default=0,
        verbose_name='탁송 요금',
    )

    withholding_tax_price = models.IntegerField(
        default=0,
        verbose_name='수행자 원천징수 금액',
    )

    employment_insurance_price = models.IntegerField(
        default=0,
        verbose_name='수행자 고용보험 금액',
    )

    additional_suggested_cost = models.PositiveIntegerField(
        default=0,
        verbose_name='의뢰인 추가 제안 요금',
    )

    additional_costs = models.ManyToManyField(
        RequestingAdditionalCost,
        related_name='contained_settlements',
        verbose_name='해당 추가 요금',
    )

    is_onsite_payment = models.BooleanField(
        verbose_name='현장 결제 유무',
    )

    class Meta:
        db_table = 'requesting_settlements'
        verbose_name = '의뢰 정산'
        verbose_name_plural = '의뢰 정산 목록'

    @property
    def direct_costs(self):
        return self.evaluation_cost + self.inspection_cost + self.delivering_cost + self.additional_suggested_cost

    @property
    def vat(self):
        costs_sum = self.evaluation_cost + self.inspection_cost + self.delivering_cost + self.additional_suggested_cost
        vat_amount = int(costs_sum * 0.1)

        return vat_amount

    @property
    def total_additional_cost(self):
        additional_cost_ids = self.additional_costs.values_list('pk', flat=True)

        result = RequestingAdditionalCost.objects \
            .filter(id__in=additional_cost_ids) \
            .aggregate(Sum('cost'))

        return result['cost__sum'] or 0

    @property
    def additional_costs_summary(self):
        additional_cost_ids = self.additional_costs.values_list('pk', flat=True)

        result = RequestingAdditionalCost.objects \
            .filter(id__in=additional_cost_ids) \
            .values_list('name', flat=True)

        return ', '.join(result)

    @property
    def fuel_costs(self):
        additional_cost_ids = self.additional_costs.values_list('pk', flat=True)

        result = RequestingAdditionalCost.objects \
            .filter(
                id__in=additional_cost_ids,
                type='주유비',
            ) \
            .aggregate(Sum('cost'))

        return result['cost__sum'] or 0

    @property
    def total_cost(self):
        return self.direct_costs + self.vat + self.total_additional_cost

    def save(self, *args, **kwargs):
        is_updating = self.pk != None

        super(RequestingSettlement, self).save(*args, **kwargs)

        if not is_updating:
            fee = 0

            fee_payment_history = self.requesting_history.fee_payment_histories \
                .filter(user=self.user) \
                .first()

            if fee_payment_history != None:
                fee = fee_payment_history.amount

            total_additional_cost = self.total_additional_cost or 0

            total_cost = self.evaluation_cost + self.inspection_cost + \
                self.delivering_cost + self.additional_suggested_cost + total_additional_cost

            if self.is_onsite_payment == False:
                revenue_amount = total_cost - fee

                withholding_tax_price = math.trunc(revenue_amount * 0.033)
                employment_insurance_price = math.trunc(revenue_amount * 0.016)

                BalanceHistory.objects.create(
                    user=self.user,
                    type='revenue',
                    amount=revenue_amount - (withholding_tax_price + employment_insurance_price),
                )

                self.withholding_tax_price = withholding_tax_price
                self.employment_insurance_price = employment_insurance_price
                self.save()

            client_referer = self.requesting_history.client.referer

            if client_referer != None and client_referer.is_agent:
                from .referer_settlement import RefererSettlement

                referer_revenue_rate = client_referer.agent_profile.referer_revenue_rate

                referer_revenue = math.trunc(fee * (referer_revenue_rate / 100))
                tax = math.trunc(referer_revenue * 0.033)

                referer_revenue = referer_revenue - tax

                RefererSettlement.objects.create(
                    user=client_referer,
                    requesting_history=self.requesting_history,
                    revenue=referer_revenue,
                    tax=tax,
                )


class DaangnRequestingSettlementManager(models.Manager):
    def get_queryset(self):
        return super(DaangnRequestingSettlementManager, self) \
            .get_queryset() \
            .exclude(Q(requesting_history__daangn_requesting_information__isnull=True))


class DaangnRequestingSettlement(RequestingSettlement):
    objects = DaangnRequestingSettlementManager()

    class Meta:
        proxy = True
        verbose_name = '당근 의뢰 정산'
        verbose_name_plural = '당근 의뢰 정산목록'
