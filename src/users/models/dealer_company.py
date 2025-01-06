import uuid

from django.db import models
from django.db.models import Q, F
from django.utils import timezone
from django.db.models.aggregates import Sum
from django.utils.crypto import get_random_string

from multiselectfield import MultiSelectField

from users.constants import DEALER_BUSINESS_CATEGORIES, DEALER_BUSINESS_ITEMS, DEALER_COMPANY_TYPES

from pcar.helpers import PreprocessUploadPath


def business_registration_image_path_getter(obj):
    return f'dealer-company/{ obj.uuid }'


class DealerCompany(models.Model):
    id = models.CharField(
        max_length=12,
        primary_key=True,
        editable=False,
        unique=True,
        verbose_name='업체 코드'
    )

    uuid = models.UUIDField(
        default=uuid.uuid4,
        verbose_name='고유 코드 (파일 업로드용)',
    )

    name = models.CharField(
        max_length=100,
        verbose_name='상호명',
    )

    type = models.CharField(
        max_length=64,
        choices=DEALER_COMPANY_TYPES,
        null=True,
        blank=True,
        verbose_name='고객(협력사) 분류',
    )

    business_opening_at = models.DateField(
        null=True,
        blank=True,
        verbose_name='거래개설일자',
    )

    business_registration_number = models.CharField(
        max_length=100,
        verbose_name='사업자 등록번호',
    )

    representative_name = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name='대표자 이름',
    )

    representative_number = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        verbose_name='대표자 연락처'
    )

    company_number = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        verbose_name='대표번호',
    )

    address = models.CharField(
        max_length=128,
        verbose_name='주소',
        null=True,
        blank=True,
    )

    person_in_charge = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        verbose_name='담당자 명',
    )

    person_in_charge_position = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        verbose_name='담당자 직위',
    )

    person_in_charge_number = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        verbose_name='담당자 연락처',
    )

    business_registration = models.ImageField(
        null=True,
        blank=True,
        upload_to=PreprocessUploadPath(business_registration_image_path_getter, 'business_registration', use_uuid_name=True),
        verbose_name='사업자등록증 사본',
    )

    email = models.EmailField(
        verbose_name='이메일 주소',
        null=True,
        blank=True,
    )

    business_items = MultiSelectField(
        max_length=32,
        choices=DEALER_BUSINESS_ITEMS,
        verbose_name='회사 아이템',
        null=True,
        blank=True,
    )

    business_categories = MultiSelectField(
        max_length=32,
        choices=DEALER_BUSINESS_CATEGORIES,
        verbose_name='사업분류',
        null=True,
        blank=True,
    )

    require_publish_bill = models.BooleanField(
        default=True,
        verbose_name='계산서 발행유무'
    )

    cooperation_level = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        verbose_name='협력도',
    )

    settlement_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='정산일',
    )

    class Meta:
        db_table = 'dealer_company'
        verbose_name = '딜러 업체'
        verbose_name_plural = '딜러 업체 목록'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = get_random_string(12)

        return super(DealerCompany, self).save(*args, **kwargs)

    @property
    def evaluation_count_current_month(self):
        from requestings.models import RequestingSettlement

        now = timezone.now()

        return RequestingSettlement.objects \
            .filter(
                Q(requesting_history__client__dealer_profile__company=self)& \
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
                Q(requesting_history__client__dealer_profile__company=self)& \
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
                Q(requesting_history__client__dealer_profile__company=self)& \
                Q(requesting_history__type='ONLY_DELIVERY')& \
                Q(requesting_end_at__year=now.year)& \
                Q(requesting_end_at__month=now.month)
            ) \
            .count()

    @property
    def total_count_current_month(self):
        from requestings.models import RequestingSettlement

        now = timezone.now()

        return RequestingSettlement.objects \
            .filter(
                Q(requesting_history__client__dealer_profile__company=self)& \
                Q(requesting_end_at__year=now.year)& \
                Q(requesting_end_at__month=now.month)
            ) \
            .count()

    @property
    def evaluation_count_avg_3_month(self):
        from requestings.models import RequestingSettlement

        now = timezone.now()

        return RequestingSettlement.objects \
            .filter(
                Q(requesting_history__client__dealer_profile__company=self)& \
                Q(requesting_history__type='EVALUATION_DELIVERY')& \
                Q(requesting_end_at__gte=(now - timezone.timedelta(days=90)))
            ) \
            .count() / 3

    @property
    def inspection_count_avg_3_month(self):
        from requestings.models import RequestingSettlement

        now = timezone.now()

        return RequestingSettlement.objects \
            .filter(
                Q(requesting_history__client__dealer_profile__company=self)& \
                Q(requesting_history__type='INSPECTION_DELIVERY')& \
                Q(requesting_end_at__gte=(now - timezone.timedelta(days=90)))
            ) \
            .count() / 3

    @property
    def delivery_count_avg_3_month(self):
        from requestings.models import RequestingSettlement

        now = timezone.now()

        return RequestingSettlement.objects \
            .filter(
                Q(requesting_history__client__dealer_profile__company=self)& \
                Q(requesting_history__type='ONLY_DELIVERY')& \
                Q(requesting_end_at__gte=(now - timezone.timedelta(days=90)))
            ) \
            .count() / 3

    @property
    def total_count_avg_3_month(self):
        from requestings.models import RequestingSettlement

        now = timezone.now()

        return RequestingSettlement.objects \
            .filter(
                Q(requesting_history__client__dealer_profile__company=self)& \
                Q(requesting_end_at__gte=(now - timezone.timedelta(days=90)))
            ) \
            .count() / 3

    @property
    def evaluation_costs_avg_3_month(self):
        from requestings.models import RequestingSettlement

        now = timezone.now()

        result = RequestingSettlement.objects \
            .filter(
                Q(requesting_history__client__dealer_profile__company=self)& \
                Q(requesting_history__type='EVALUATION_DELIVERY')& \
                Q(requesting_end_at__gte=(now - timezone.timedelta(days=90)))
            ) \
            .aggregate(cost_sum=Sum('evaluation_cost'))

        return (result['cost_sum'] or 0) / 3

    @property
    def inspection_costs_avg_3_month(self):
        from requestings.models import RequestingSettlement

        now = timezone.now()

        result = RequestingSettlement.objects \
            .filter(
                Q(requesting_history__client__dealer_profile__company=self)& \
                Q(requesting_history__type='INSPECTION_DELIVERY')& \
                Q(requesting_end_at__gte=(now - timezone.timedelta(days=90)))
            ) \
            .aggregate(cost_sum=Sum('inspection_cost'))

        return (result['cost_sum'] or 0) / 3

    @property
    def delivery_costs_avg_3_month(self):
        from requestings.models import RequestingSettlement

        now = timezone.now()

        result = RequestingSettlement.objects \
            .filter(
                Q(requesting_history__client__dealer_profile__company=self)& \
                Q(requesting_history__type='ONLY_DELIVERY')& \
                Q(requesting_end_at__gte=(now - timezone.timedelta(days=90)))
            ) \
            .aggregate(cost_sum=Sum('delivering_cost'))

        return (result['cost_sum'] or 0) / 3

    @property
    def total_costs_avg_3_month(self):
        from requestings.models import RequestingSettlement

        now = timezone.now()

        result = RequestingSettlement.objects \
            .filter(
                Q(requesting_history__client__dealer_profile__company=self)& \
                Q(requesting_history__type='ONLY_DELIVERY')& \
                Q(requesting_end_at__gte=(now - timezone.timedelta(days=90)))
            ) \
            .annotate(total_cost=F('evaluation_cost') + F('inspection_cost') + F('delivering_cost')) \
            .aggregate(cost_sum=Sum('total_cost'))

        return (result['cost_sum'] or 0) / 3

    @property
    def evaluation_costs_current_month(self):
        from requestings.models import RequestingSettlement

        now = timezone.now()

        result = RequestingSettlement.objects \
            .filter(
                Q(requesting_history__client__dealer_profile__company=self)& \
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
                Q(requesting_history__client__dealer_profile__company=self)& \
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
                Q(requesting_history__client__dealer_profile__company=self)& \
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
                Q(requesting_history__client__dealer_profile__company=self)& \
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
                Q(requesting_history__client__dealer_profile__company=self)& \
                Q(requesting_history__type='EVALUATION_DELIVERY')
            ) \
            .aggregate(cost_sum=Sum('evaluation_cost'))

        return result['cost_sum'] or 0

    @property
    def acc_inspection_costs(self):
        from requestings.models import RequestingSettlement

        result = RequestingSettlement.objects \
            .filter(
                Q(requesting_history__client__dealer_profile__company=self)& \
                Q(requesting_history__type='INSPECTION_DELIVERY')
            ) \
            .aggregate(cost_sum=Sum('inspection_cost'))

        return result['cost_sum'] or 0

    @property
    def acc_delivery_costs(self):
        from requestings.models import RequestingSettlement

        result = RequestingSettlement.objects \
            .filter(
                Q(requesting_history__client__dealer_profile__company=self)& \
                Q(requesting_history__type='ONLY_DELIVERY')
            ) \
            .aggregate(cost_sum=Sum('delivering_cost'))

        return result['cost_sum'] or 0

    @property
    def acc_total_costs(self):
        from requestings.models import RequestingSettlement

        result = RequestingSettlement.objects \
            .filter(
                Q(requesting_history__client__dealer_profile__company=self)& \
                Q(requesting_history__type='ONLY_DELIVERY')
            ) \
            .annotate(total_cost=F('evaluation_cost') + F('inspection_cost') + F('delivering_cost')) \
            .aggregate(cost_sum=Sum('total_cost'))

        return result['cost_sum'] or 0
