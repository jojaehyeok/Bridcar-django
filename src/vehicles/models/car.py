import uuid

from django.db import models

from django_random_id_model import RandomIDModel

from requestings.models import RequestingHistory

from vehicles.constants import CAR_CLASSIFICATIONS, CAR_TRANSMISSIONS

from pcar.helpers import PreprocessUploadPath


def image_path_getter(instance):
    return f'vehicles/cars/{ instance.uuid }'


class Car(RandomIDModel, models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    requesting_history = models.OneToOneField(
        RequestingHistory,
        on_delete=models.CASCADE,
        related_name='car',
        verbose_name='해당 차량의 의뢰',
    )

    number = models.CharField(
        max_length=36,
        verbose_name='차량번호',
    )

    type = models.CharField(
        max_length=50,
        verbose_name='차종',
        null=True,
        blank=True,
    )

    transmission = models.CharField(
        max_length=10,
        choices=CAR_TRANSMISSIONS,
        verbose_name='변속기 분류',
        null=True,
        blank=True,
    )

    classification = models.CharField(
        max_length=10,
        choices=CAR_CLASSIFICATIONS,
        verbose_name='차량 분류',
        null=True,
        blank=True,
    )

    mileage = models.PositiveBigIntegerField(
        default=0,
        verbose_name='주행거리',
    )

    color = models.CharField(
        max_length=100,
        verbose_name='차량 색상',
        null=True,
        blank=True,
    )

    registration_image = models.ImageField(
        upload_to=PreprocessUploadPath(
            image_path_getter,
            filename_prefix='registration-image',
            use_uuid_name=True,
        ),
        verbose_name='차량 등록증 이미지',
        null=True,
        blank=True,
    )

    instrument_panel_image = models.ImageField(
        upload_to=PreprocessUploadPath(
            image_path_getter,
            filename_prefix='instrument-panel-image',
            use_uuid_name=True,
        ),
        verbose_name='계기판 이미지',
        null=True,
        blank=True,
    )

    identification_number_image = models.ImageField(
        upload_to=PreprocessUploadPath(
            image_path_getter,
            filename_prefix='identification-number-image',
            use_uuid_name=True,
        ),
        verbose_name='차대번호 라벨',
        null=True,
        blank=True,
    )

    back_image = models.ImageField(
        upload_to=PreprocessUploadPath(
            image_path_getter,
            filename_prefix='back-image',
            use_uuid_name=True,
        ),
        verbose_name='차량 후방 이미지',
        null=True,
        blank=True,
    )

    external_car_image_url = models.URLField(
        null=True,
        blank=True,
        verbose_name='차량 이미지 (외부 업로드)',
    )

    class Meta:
        db_table = 'cars'
        verbose_name = '자동차'
        verbose_name_plural = '자동차 목록'

    def __str__(self):
        return self.number
