from django.db import models
from django.db.models import F, Q
from django.utils import timezone
from django.db.models.aggregates import Sum

from multiselectfield import MultiSelectField

from pcar.helpers import PreprocessUploadPath

from locations.models import CommonLocation

from users.constants import DEALER_BUSINESS_CATEGORIES, DEALER_BUSINESS_ITEMS

from .user import User
from .dealer_company import DealerCompany


class DealerProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='dealer_profile',
    )

    company = models.ForeignKey(
        DealerCompany,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='dealers',
        verbose_name='소속 업체',
    )

    main_warehouses = models.ManyToManyField(
        CommonLocation,
        null=True,
        blank=True,
        verbose_name='주 입고지',
        related_name='dealer_profiles',
    )

    memo = models.TextField(
        null=True,
        blank=True,
        verbose_name='기타 메모'
    )

    basic_evaluation_cost = models.PositiveIntegerField(
        default=50000,
        verbose_name='기본 평카 비용',
    )

    basic_inspection_cost= models.PositiveIntegerField(
        default=50000,
        verbose_name='기본 검수 비용',
    )

    cooperation_level = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        verbose_name='협력도 (개인)',
    )

    settlement_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='정산일 (개인)',
        help_text='회사 소속의 회원일 경우 공란',
    )

    is_alimtalk_receiving = models.BooleanField(
        default=True,
        verbose_name='카카오 알림톡 수신 여부',
    )

    class Meta:
        db_table = 'dealer_profiles'
        verbose_name = '딜러'
        verbose_name_plural = '딜러 목록'

    def __str__(self):
        return self.user.name

    @property
    def evaluation_count_current_month(self):
        from requestings.models import RequestingSettlement

        now = timezone.now()

        return RequestingSettlement.objects \
            .filter(
                Q(requesting_history__client__dealer_profile=self)& \
                Q(requesting_history__type='EVALUATION_DELIVERY')& \
                Q(requesting_end_at__year=now.year)& \
                Q(requesting_end_at__month=now.month)
            ) \
            .count()

    @property
    def inspection_count_current_month(self):
        from requestings.models import RequestingSettlement

        now = timezone.now()

        return RequestingSettlement.objects \
            .filter(
                Q(requesting_history__client__dealer_profile=self)& \
                Q(requesting_history__type='INSPECTION_DELIVERY')& \
                Q(requesting_end_at__year=now.year)& \
                Q(requesting_end_at__month=now.month)
            ) \
            .count()

    @property
    def delivery_count_current_month(self):
        from requestings.models import RequestingSettlement

        now = timezone.now()

        return RequestingSettlement.objects \
            .filter(
                Q(requesting_history__client__dealer_profile=self)& \
                Q(requesting_history__type='ONLY_DELIVERY')& \
                Q(requesting_end_at__year=now.year)& \
                Q(requesting_end_at__month=now.month)
            ) \
            .count()

    @property
    def evaluation_costs_current_month(self):
        from requestings.models import RequestingSettlement

        now = timezone.now()

        result = RequestingSettlement.objects \
            .filter(
                Q(requesting_history__client__dealer_profile=self)& \
                Q(requesting_history__type='EVALUATION_DELIVERY')& \
                Q(requesting_end_at__year=now.year)& \
                Q(requesting_end_at__month=now.month)
            ) \
            .aggregate(cost_sum=Sum('evaluation_cost'))

        return result['cost_sum'] or 0

    @property
    def inspection_costs_current_month(self):
        from requestings.models import RequestingSettlement

        now = timezone.now()

        result = RequestingSettlement.objects \
            .filter(
                Q(requesting_history__client__dealer_profile=self)& \
                Q(requesting_history__type='INSPECTION_DELIVERY')& \
                Q(requesting_end_at__year=now.year)& \
                Q(requesting_end_at__month=now.month)
            ) \
            .aggregate(cost_sum=Sum('inspection_cost'))

        return result['cost_sum'] or 0

    @property
    def delivery_costs_current_month(self):
        from requestings.models import RequestingSettlement

        now = timezone.now()

        result = RequestingSettlement.objects \
            .filter(
                Q(requesting_history__client__dealer_profile=self)& \
                Q(requesting_history__type='ONLY_DELIVERY')& \
                Q(requesting_end_at__year=now.year)& \
                Q(requesting_end_at__month=now.month)
            ) \
            .aggregate(cost_sum=Sum('delivering_cost'))

        return result['cost_sum'] or 0

    @property
    def total_costs_current_month(self):
        from requestings.models import RequestingSettlement

        now = timezone.now()

        result = RequestingSettlement.objects \
            .filter(
                Q(requesting_history__client__dealer_profile=self)& \
                Q(requesting_history__type='ONLY_DELIVERY')& \
                Q(requesting_end_at__year=now.year)& \
                Q(requesting_end_at__month=now.month)
            ) \
            .annotate(total_cost=F('evaluation_cost') + F('inspection_cost') + F('delivering_cost')) \
            .aggregate(cost_sum=Sum('total_cost'))

        return result['cost_sum'] or 0

    @property
    def acc_evaluation_costs(self):
        from requestings.models import RequestingSettlement

        result = RequestingSettlement.objects \
            .filter(
                Q(requesting_history__client__dealer_profile=self)& \
                Q(requesting_history__type='EVALUATION_DELIVERY')
            ) \
            .aggregate(cost_sum=Sum('evaluation_cost'))

        return result['cost_sum'] or 0

    @property
    def acc_inspection_costs(self):
        from requestings.models import RequestingSettlement

        result = RequestingSettlement.objects \
            .filter(
                Q(requesting_history__client__dealer_profile=self)& \
                Q(requesting_history__type='INSPECTION_DELIVERY')
            ) \
            .aggregate(cost_sum=Sum('inspection_cost'))

        return result['cost_sum'] or 0

    @property
    def acc_delivery_costs(self):
        from requestings.models import RequestingSettlement

        result = RequestingSettlement.objects \
            .filter(
                Q(requesting_history__client__dealer_profile=self)& \
                Q(requesting_history__type='ONLY_DELIVERY')
            ) \
            .aggregate(cost_sum=Sum('delivering_cost'))

        return result['cost_sum'] or 0

    @property
    def acc_total_costs(self):
        from requestings.models import RequestingSettlement

        result = RequestingSettlement.objects \
            .filter(
                Q(requesting_history__client__dealer_profile=self)& \
                Q(requesting_history__type='ONLY_DELIVERY')
            ) \
            .annotate(total_cost=F('evaluation_cost') + F('inspection_cost') + F('delivering_cost')) \
            .aggregate(cost_sum=Sum('total_cost'))

        return result['cost_sum'] or 0
