from django.db import models

from pcar.helpers import PreprocessUploadPath


def template_file_getter(obj):
    return f'external-evaluation-templates'


class ExternalEvaluationTemplate(models.Model):
    name = models.CharField(
        max_length=50,
        verbose_name='템플릿 이름',
    )

    file = models.FileField(
        upload_to=PreprocessUploadPath(template_file_getter, use_uuid_name=True),
    )

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'external_evaluation_templates'
        verbose_name = '외부 평가지 양식'
        verbose_name_plural = '외부 평가지 양식 목록'
