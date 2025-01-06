from django.db import models

from users.models import Dealer

from pcar.helpers import PreprocessUploadPath

from .requesting_history import RequestingHistory


def review_image_path_getter(obj):
    return f'reviews'


class Review(models.Model):
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='작성 시각',
    )

    name = models.CharField(
        max_length=32,
        null=True,
        blank=True,
        verbose_name='작성자 이름 (필수 아님, 의뢰로 등록된 경우 의뢰자 이름 우선)',
    )

    requesting_history = models.OneToOneField(
        RequestingHistory,
        on_delete=models.SET_NULL,
        related_name='review',
        verbose_name='대상 의뢰',
        null=True,
        blank=True,
    )

    content = models.TextField(
        max_length=500,
        verbose_name='리뷰 내용',
    )

    is_exposing_to_dealer = models.BooleanField(
        default=False,
        verbose_name='의뢰인용 앱 메인 노출 유무',
    )

    class Meta:
        db_table = 'reviews'
        verbose_name = '리뷰'
        verbose_name_plural = '리뷰 목록'


class ReviewImage(models.Model):
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='대상 이미지',
    )

    image = models.ImageField(
        upload_to=PreprocessUploadPath(review_image_path_getter, use_uuid_name=True),
        null=True,
        blank=True,
        verbose_name='리뷰 이미지',
    )

    class Meta:
        db_table = 'review_images'
        verbose_name = '리뷰 이미지'
        verbose_name_plural = '리뷰 이미지 목록'
