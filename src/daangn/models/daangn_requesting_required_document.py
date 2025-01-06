from django.db import models

from daangn.models import DaangnRequestingInformation


class DaangnRequestingRequiredDocument(models.Model):
    daangn_requesting_information = models.ForeignKey(
        DaangnRequestingInformation,
        on_delete=models.CASCADE,
        verbose_name='해당 당근 의뢰 정보',
        related_name='required_documents',
    )

    key = models.CharField(
        max_length=128,
        verbose_name='서류 구분 값'
    )

    title = models.CharField(
        max_length=128,
        verbose_name='서류 제목',
    )

    description = models.CharField(
        max_length=256,
        verbose_name='서류에 대한 설명',
    )

    is_optional = models.BooleanField(
        default=False,
        verbose_name='선택 사항 여부',
        blank=True,
    )

    def __str__(self):
        return f'필요 서류 ({ self.title })'

    class Meta:
        db_table = 'daangn_requesting_required_documents'
        verbose_name = '당근 의뢰 필요 서류'
        verbose_name_plural = '당근 의뢰 필요 서류 목록'
