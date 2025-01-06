from django.db import models

from ckeditor_uploader.fields import RichTextUploadingField

from boards.constants import AGREEMENT_TYPES

from pcar.helpers import PreprocessUploadPath


class Agreement(models.Model):
    type = models.CharField(
        choices=AGREEMENT_TYPES,
        max_length=32,
        unique=True,
        verbose_name='약관 종류',
    )

    content = RichTextUploadingField(
        verbose_name='내용'
    )

    class Meta:
        db_table = 'agreements'
        verbose_name = '약관'
        verbose_name_plural = '약관 목록'

    def __str__(self):
        return dict(AGREEMENT_TYPES)[self.type]
