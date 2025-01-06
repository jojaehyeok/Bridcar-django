# Generated by Django 4.0.6 on 2023-03-20 13:58

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0031_agentprofile_dotori_status_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='agentprofile',
            name='referer_reward_rate',
            field=models.FloatField(default=5, validators=[django.core.validators.MaxValueValidator(30), django.core.validators.MinValueValidator(1)], verbose_name='홍보 수익금률 (%)'),
        ),
    ]