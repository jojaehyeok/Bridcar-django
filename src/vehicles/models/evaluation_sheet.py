from django.db import models

from pcar.helpers import PreprocessUploadPath

from vehicles.models import Car

from requestings.models import ExternalEvaluationTemplate


def image_path_getter(instance):
    return f'vehicles/cars/{ instance.car.uuid }'


class CarEvaluationSheet(models.Model):
    car = models.ForeignKey(
        Car,
        on_delete=models.CASCADE,
        related_name='evaluation_sheets',
    )

    image = models.ImageField(
        upload_to=PreprocessUploadPath(image_path_getter, 'car_evaluation_sheets'),
        verbose_name='평가지 파일'
    )

    class Meta:
        db_table = 'car_evaluation_sheets'
        verbose_name = '진단 평가지'
        verbose_name_plural = '진단평가지 목록'

    def __str__(self):
        return f'{ self.car.number } 차량 진단평가지'
