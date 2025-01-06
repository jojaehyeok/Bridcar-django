import uuid

from django.db import models

from vehicles.models import Car


class CarhistoryAccidentInsuranceHistory(models.Model):
    insurance_at = models.DateField(verbose_name='보험처리 날짜')

    total_cost = models.PositiveIntegerField(
        default=0,
        verbose_name='총 보험처리 금액',
    )

    parts_cost = models.PositiveIntegerField(
        default=0,
        verbose_name='부품 금액',
    )

    labor_cost = models.PositiveIntegerField(
        default=0,
        verbose_name='공임 비용',
    )

    painting_cost = models.PositiveIntegerField(
        default=0,
        verbose_name='도장 비용',
    )

    class Meta:
        db_table = 'carhistory_accident_insurance_histories'
        verbose_name = '사고 보험처리 목록'
        verbose_name_plural = '사고 보험처리 목록 내역'


class CarhistoryResult(models.Model):
    car = models.OneToOneField(
        Car,
        on_delete=models.CASCADE,
        related_name='carhistory_result',
        verbose_name='대상 차량',
    )

    is_scrapping = models.BooleanField(
        default=True,
        verbose_name='현재 크롤링 진행중 여부',
    )

    scrapping_at = models.DateTimeField(
        verbose_name='스크래핑 한 시각',
        null=True,
        blank=True,
    )

    error_message = models.TextField(
        null=True,
        blank=True,
        verbose_name='에러메시지 (스크래핑 에러 발생시)',
    )

    insurance_with_my_damages = models.ManyToManyField(
        CarhistoryAccidentInsuranceHistory,
        null=True,
        blank=True,
        related_name='carhistory_as_my_damage',
        verbose_name='내 차 사고 발생 내역',
    )

    insurance_with_opposite_damages = models.ManyToManyField(
        CarhistoryAccidentInsuranceHistory,
        null=True,
        blank=True,
        related_name='carhistory_as_opposite_damage',
        verbose_name='상대 차 사고 발생 내역',
    )

    class Meta:
        db_table = 'carhistory_results'
        verbose_name = '카히스토리 조회 결과'
        verbose_name_plural = '카히스토리 조회 결과 목록'


class CarhistoryOwnerChangeHistory(models.Model):
    carhistory_result = models.ForeignKey(
        CarhistoryResult,
        on_delete=models.CASCADE,
        related_name='owner_change_histories',
        verbose_name='대상 카히스토리 결과',
    )

    changed_at = models.DateField(verbose_name='변경 시기')

    changing_type = models.CharField(
        max_length=30,
        verbose_name='변경 구분',
    )

    changed_car_number = models.CharField(
        max_length=30,
        verbose_name='변경 후 차량 번호',
    )

    changing_usage = models.CharField(
        max_length=30,
        verbose_name='변경 후 차량 용도',
    )

    class Meta:
        db_table = 'carhistory_owner_change_histories'
        verbose_name = '소유자 변경 내역'
        verbose_name_plural = '소유자 변경 내역 목록'


