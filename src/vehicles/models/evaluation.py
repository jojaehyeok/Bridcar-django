from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

from pcar.helpers import PreprocessUploadPath

from .car import Car


def car_evaluation_image_path_getter(instance):
    return f'vehicles/cars/{ instance.uuid }/evaluation-images'


class CarEvaluationResult(models.Model):
    car = models.OneToOneField(
        Car,
        on_delete=models.CASCADE,
        related_name='evaluation_result',
        verbose_name='대상 차량',
    )

    color = models.CharField(
        max_length=100,
        verbose_name='차량 색상',
        null=True,
        blank=True,
    )

    mileage = models.PositiveBigIntegerField(
        default=0,
        verbose_name='주행거리',
    )

    general_key_counts = models.IntegerField(
        default=0,
        verbose_name='일반 차키 갯수',
    )

    smart_key_counts = models.IntegerField(
        default=0,
        verbose_name='스마트 차키 갯수',
    )

    folding_key_counts = models.IntegerField(
        default=0,
        verbose_name='폴딩 차키 갯수',
    )

    special_key_counts = models.IntegerField(
        default=0,
        verbose_name='특수 차키 갯수',
    )

    required_exterior_paint_counts = models.IntegerField(
        default=0,
        verbose_name='필요 외판 도색',
    )

    wheel_scratch_counts = models.IntegerField(
        default=0,
        verbose_name='휠기스',
    )

    remaining_front_tire = models.IntegerField(
        default=100,
        validators=[
            MaxValueValidator(100),
            MinValueValidator(0),
        ],
        verbose_name='앞 타이어 잔존량',
    )

    remaining_rear_tire = models.IntegerField(
        default=100,
        validators=[
            MaxValueValidator(100),
            MinValueValidator(0),
        ],
        verbose_name='뒤 타이어 잔존량',
    )

    statuses = models.JSONField(
        default=[[]],
        verbose_name='자동차 상태 (외판체크)',
    )

    have_instrument_panel_warning = models.BooleanField(
        default=False,
        verbose_name='계기판 경고등 있음',
    )

    instrument_panel_warning_memo = models.TextField(
        verbose_name='계기판 경고등 관련 메모',
        null=True,
        blank=True,
    )

    have_option_malfunction = models.BooleanField(
        default=False,
        verbose_name='옵션 기능 작동 이상',
    )

    option_malfunction_memo = models.TextField(
        verbose_name='옵션 기능 작동 이상 관련 메모',
        null=True,
        blank=True,
    )

    have_leakage = models.BooleanField(
        default=False,
        verbose_name='누유 있음',
    )

    leakage_memo = models.TextField(
        verbose_name='누유 관련 메모',
        null=True,
        blank=True,
    )

    have_abnormal_while_driving = models.BooleanField(
        default=False,
        verbose_name='주행중 이상 증상',
    )

    abnormal_while_driving_memo = models.TextField(
        verbose_name='주행중 이상 증상 관련 메모',
        null=True,
        blank=True,
    )

    estimated_recovery_cost = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='예상 복구 비용',
    )

    drivers_side_mirror_cover_marker = models.JSONField(
        null=True,
        blank=True,
        verbose_name='운전석 사이드 미러 덮개 데미지',
    )

    drivers_side_mirror_mirror_marker = models.JSONField(
        null=True,
        blank=True,
        verbose_name='운전석 사이드 미러 거울 데미지',
    )

    drivers_side_mirror_repeater_marker = models.JSONField(
        null=True,
        blank=True,
        verbose_name='운전석 사이드 미러 리피터 데미지',
    )

    passenger_side_mirror_cover_marker = models.JSONField(
        null=True,
        blank=True,
        verbose_name='조수석 사이드 미러 덮개 데미지',
    )

    passenger_side_mirror_mirror_marker = models.JSONField(
        null=True,
        blank=True,
        verbose_name='조수석 사이드 미러 거울 데미지',
    )

    passenger_side_mirror_repeater_marker = models.JSONField(
        null=True,
        blank=True,
        verbose_name='조수석 사이드 미러 리피터 데미지',
    )

    memo = models.TextField(
        max_length=1000,
        verbose_name='기타 의견',
        null=True,
        blank=True,
    )

    class Meta:
        db_table = 'car_evaluation_results'
        verbose_name = '진단 평가'
        verbose_name_plural = '진단 평가 목록'

    def __str__(self):
        return f'{ self.car.number } 차량 진단 평가'


class CarEvaluationImage(models.Model):
    evaluation_result = models.ForeignKey(
        CarEvaluationResult,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='대상 차량 평가',
    )

    uuid = models.CharField(
        max_length=256,
        verbose_name='이미지 ID (Picker 라이브러리 id)',
    )

    image = models.ImageField(
        upload_to=PreprocessUploadPath(car_evaluation_image_path_getter, use_uuid_name=True),
        verbose_name='이미지',
    )

    class Meta:
        db_table = 'car_evaluation_images'
        verbose_name = '차량 평가 사진'
        verbose_name_plural = '차량 평가 사진 목록'

    def __str__(self):
        return f'{ self.evaluation_result.car.number } 차량 이미지'
