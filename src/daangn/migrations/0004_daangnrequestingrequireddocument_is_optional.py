# Generated by Django 4.0.6 on 2024-10-28 13:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('daangn', '0003_daangnrequestingrequireddocument'),
    ]

    operations = [
        migrations.AddField(
            model_name='daangnrequestingrequireddocument',
            name='is_optional',
            field=models.BooleanField(blank=True, default=False, verbose_name='선택 사항 여부'),
        ),
    ]
