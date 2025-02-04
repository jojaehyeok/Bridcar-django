# Generated by Django 4.0.6 on 2023-02-19 16:43

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0010_agentprofile_insurance_expiry_date_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='agentprofile',
            name='insurance_expiry_date',
            field=models.DateField(default=django.utils.timezone.now, help_text='보험 만료 시 해당 평카인은 오더에 배차가 불가능합니다', verbose_name='보험 만료 일시'),
            preserve_default=False,
        ),
    ]
