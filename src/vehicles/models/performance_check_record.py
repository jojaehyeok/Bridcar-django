from django.db import models

from pcar.helpers import PreprocessUploadPath

from vehicles.models import Car

from requestings.models import ExternalEvaluationTemplate


def file_path_getter(instance):
    return f'vehicles/cars/{ instance.car.uuid }'


class PerformanceCheckRecord(models.Model):
    car = models.ForeignKey(
        Car,
        on_delete=models.CASCADE,
        related_name='performance_check_records',
    )

    file = models.FileField(
        upload_to=PreprocessUploadPath(file_path_getter, use_uuid_name=True),
        verbose_name='성능점검기록부 파일'
    )

    class Meta:
        db_table = 'performance_check_records'
        verbose_name = '성능점검기록부'
        verbose_name_plural = '성능점검기록부 목록'

    def __str__(self):
        return f'{ self.car.number } 차량 진단평가지'
