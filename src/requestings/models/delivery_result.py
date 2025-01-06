from django.db import models

from requestings.models import RequestingHistory
from requestings.constants import CAR_BASIC_IMAGE_TYPES

from pcar.helpers import PreprocessUploadPath


def delivery_asset_image_path_getter(obj):
    return f'delivery-assets'

def car_condition_image_path_getter(obj):
    return f'delivery-assets'


class DeliveryAsset(models.Model):
    image = models.ImageField(
        upload_to=PreprocessUploadPath(delivery_asset_image_path_getter, use_uuid_name=True),
        verbose_name='이미지'
    )

    class Meta:
        db_table = 'delivery_assets'
        verbose_name = '탁송 관련 에셋'
        verbose_name_plural = '탁송 관련 에셋 목록'


class DeliveryResult(models.Model):
    requesting_history = models.OneToOneField(
        RequestingHistory,
        on_delete=models.CASCADE,
        related_name='delivery_result',
        verbose_name='대상 의뢰',
    )

    mileage_before_delivery = models.IntegerField(
        verbose_name='탁송 전 현재 주행거리',
    )

    mileage_after_delivery = models.IntegerField(
        verbose_name='차량 입고시 주행거리',
        null=True,
        blank=True,
    )

    memo = models.TextField(
        verbose_name='특이사항',
        null=True,
        blank=True,
    )

    class Meta:
        db_table = 'delivery_results'
        verbose_name = '탁송 결과'
        verbose_name_plural = '탁송 결과 목록'


class CarBasicImage(models.Model):
    delivery_result = models.ForeignKey(
        DeliveryResult,
        on_delete=models.CASCADE,
        related_name='car_basic_images',
        verbose_name='기본 사진 목록',
    )

    is_before_delivery = models.BooleanField(verbose_name='탁송 전 사진')

    image = models.ImageField(
        upload_to=PreprocessUploadPath(car_condition_image_path_getter, use_uuid_name=True),
        verbose_name='차량 상태 이미지'
    )

    type = models.CharField(
        default='EXTERIOR',
        choices=CAR_BASIC_IMAGE_TYPES,
        max_length=128,
        verbose_name='사진 구분',
    )

    sub_type = models.CharField(
        max_length=128,
        verbose_name='사진 보조 구분',
        null=True,
        blank=True,
    )

    class Meta:
        db_table = 'car_basic_images'
        verbose_name = '기본 사진'
        verbose_name_plural = '기본 사진 목록'


class CarAccidentSiteImage(models.Model):
    delivery_result = models.ForeignKey(
        DeliveryResult,
        on_delete=models.CASCADE,
        related_name='car_accident_site_images',
        verbose_name='대상 탁송 결과',
    )

    is_before_delivery = models.BooleanField(verbose_name='탁송 전 사진')

    image = models.ImageField(
        upload_to=PreprocessUploadPath(car_condition_image_path_getter, use_uuid_name=True),
        verbose_name='차량 상태 이미지'
    )

    class Meta:
        db_table = 'car_accident_site_images'
        verbose_name = '사고 부위 사진'
        verbose_name_plural = '사고 부위 사진 목록'
