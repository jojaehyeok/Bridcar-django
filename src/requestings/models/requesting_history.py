from functools import reduce

from django.db import models
from django.db.models import Q

from django_random_id_model import RandomIDModel

from phonenumber_field.modelfields import PhoneNumberField

from users.models import Agent, Dealer, BalanceHistory

from locations.models import CommonLocation
from locations.utils import get_driving_distance_with_kakao

from ..constants import REQUESTING_TYPES, REQUESTING_STATUS

class RequestingHistory(RandomIDModel):
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='의뢰 접수 일시'
    )

    type = models.CharField(
        max_length=32,
        choices=REQUESTING_TYPES,
        verbose_name='의뢰 형태',
    )

    status = models.CharField(
        max_length=64,
        choices=REQUESTING_STATUS,
        verbose_name='의뢰 상태',
    )

    client = models.ForeignKey(
        Dealer,
        on_delete=models.SET_NULL,
        verbose_name='의뢰인',
        related_name='requestings',
        null=True,
        blank=True,
    )

    external_client_name = models.CharField(
        max_length=32,
        verbose_name='원 의뢰자 이름 (위탁 의뢰건만)',
        null=True,
        blank=True,
    )

    external_client_mobile_number = PhoneNumberField(
        verbose_name='원 의뢰자 핸드폰번호 (위탁 의뢰건만)',
        null=True,
        blank=True,
    )

    agent = models.ForeignKey(
        Agent,
        on_delete=models.CASCADE,
        verbose_name='담당 평가사 (탁송건일 경우 공란)',
        related_name='allocation_requestings',
        null=True,
        blank=True,
        help_text='탁송만 하는 의뢰일 경우 공란으로 두세요',
    )

    is_delivery_transferred = models.BooleanField(
        default=False,
        verbose_name='탁송 양도 여부',
    )

    fee_payment_histories = models.ManyToManyField(
        BalanceHistory,
        null=True,
        blank=True,
        related_name='fee_payment_histories',
        verbose_name='에이전트 수수료 결제 기록',
    )

    deliverer = models.ForeignKey(
        Agent,
        on_delete=models.CASCADE,
        verbose_name='담당 탁송기사',
        related_name='allocation_as_deliverer_requestings',
        null=True,
        blank=True,
    )

    skip_fee_for_deliverer = models.BooleanField(
        verbose_name='탁송기사 수수료 면제 여부',
        default=False,
    )

    reservation_date = models.DateTimeField(
        verbose_name='예약 날짜',
        null=True,
        blank=True,
    )

    estimated_service_date = models.DateTimeField(
        verbose_name='서비스 예정 시작 날짜',
        null=True,
        blank=True,
    )

    source_location = models.ForeignKey(
        CommonLocation,
        on_delete=models.CASCADE,
        verbose_name='출발지 위치',
        related_name='requestings_used_as_source',
    )

    destination_location = models.ForeignKey(
        CommonLocation,
        on_delete=models.CASCADE,
        verbose_name='도착지 위치',
        related_name='requestings_used_as_destination',
    )

    distance_between_source_destination = models.FloatField(
        default=0,
        verbose_name='출발지와 목적지간 거리',
    )

    stopovers = models.ManyToManyField(
        CommonLocation,
        null=True,
        blank=True,
        related_name='requestings_used_as_stopover',
        verbose_name='경유지',
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
        null=True,
    )

    additional_suggested_cost = models.PositiveIntegerField(
        default=0,
        verbose_name='의뢰인 추가 제안 요금',
    )

    evaluation_finished_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='평카(검수) 일시',
    )

    confirmation_inspection_result_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='의뢰인 검수 결과 확인 일시',
    )

    is_onsite_payment = models.BooleanField(
        verbose_name='현장 결제 유무',
    )

    delivery_proceed_decided_at = models.DateTimeField(
        verbose_name='의뢰자 탁송 결정 시각',
        null=True,
        blank=True,
    )

    has_agent_delivery_start = models.BooleanField(
        default=False,
        verbose_name='의뢰인의 탁송 출발 여부',
    )

    hook_url = models.URLField(
        null=True,
        blank=True,
        verbose_name='웹훅 URL',
    )

    memo = models.TextField(
        max_length=300,
        verbose_name='메모 (특이사항)',
        null=True,
        blank=True,
    )

    class Meta:
        db_table = 'requesting_histories'
        verbose_name = '의뢰'
        verbose_name_plural = '의뢰 목록'

    def __str__(self):
        return_str = ''

        if hasattr(self, 'car'):
            return_str = f'{ self.car.number } 차량 { dict(REQUESTING_TYPES)[self.type] } 의뢰'

        if hasattr(self, 'daangn_requesting_information'):
            return_str = '🥕 ' + return_str

        return return_str

    @property
    def total_cost(self):
        result = 0
        total_additional_cost = reduce(lambda acc, cur: acc + cur.cost, self.additional_costs.all(), 0)

        if self.type == 'EVALUATION_DELIVERY':
            result += (self.evaluation_cost or 0)
        elif self.type == 'INSPECTION_DELIVERY':
            result += (self.inspection_cost or 0)

        stopover_cost = self.stopovers.count() * 5000

        result += (self.delivering_cost or 0) + stopover_cost + \
            (self.additional_suggested_cost or 0) + total_additional_cost

        return result


    def save(self, *args, **kwargs):
        if self.pk == None:
            if self.type == 'EVALUATION_DELIVERY':
                if not self.evaluation_cost:
                    self.evaluation_cost = self.client.dealer_profile.basic_evaluation_cost
            elif self.type == 'INSPECTION_DELIVERY':
                if not self.inspection_cost:
                    self.inspection_cost = self.client.dealer_profile.basic_inspection_cost

            self.distance_between_source_destination = get_driving_distance_with_kakao(
                { 'latitude': self.source_location.coord[1], 'longitude': self.source_location.coord[0], },
                { 'latitude': self.destination_location.coord[1], 'longitude': self.destination_location.coord[0], },
            )

        super(RequestingHistory, self).save(*args, **kwargs)


class FinishedRequestingHistoryManager(models.Manager):
    def get_queryset(self):
        return super(FinishedRequestingHistoryManager, self) \
            .get_queryset() \
            .filter(Q(status='DONE'))


class FinishedRequestingHistory(RequestingHistory):
    objects = FinishedRequestingHistoryManager()

    class Meta:
        proxy = True
        verbose_name = '완료된 의뢰'
        verbose_name_plural = '완료된 의뢰 목록'


class DaangnRequestingHistoryManager(models.Manager):
    def get_queryset(self):
        return super(DaangnRequestingHistoryManager, self) \
            .get_queryset() \
            .filter(daangn_requesting_information__isnull=False)


class DaangnRequestingHistory(RequestingHistory):
    objects = DaangnRequestingHistoryManager()

    class Meta:
        proxy = True
        verbose_name = '당근마켓 의뢰'
        verbose_name_plural = '당근마켓 의뢰목록'


class FinishedDaangnRequestingHistoryManager(models.Manager):
    def get_queryset(self):
        return super(FinishedDaangnRequestingHistoryManager, self) \
            .get_queryset() \
            .filter(
                Q(status='DONE')& \
                Q(daangn_requesting_information__isnull=False)
            )


class FinishedDaangnRequestingHistory(RequestingHistory):
    objects = FinishedDaangnRequestingHistoryManager()

    class Meta:
        proxy = True
        verbose_name = '완료된 당근마켓 의뢰'
        verbose_name_plural = '완료된 당근마켓 의뢰목록'
