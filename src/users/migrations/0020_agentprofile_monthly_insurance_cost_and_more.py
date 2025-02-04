# Generated by Django 4.0.6 on 2023-03-12 05:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0019_dealercompany_cooperation_level_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='agentprofile',
            name='monthly_insurance_cost',
            field=models.PositiveIntegerField(default=0, verbose_name='월 보험금'),
        ),
        migrations.AddField(
            model_name='agentprofile',
            name='training_completion_date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='평카인 교육 수료일'),
        ),
        migrations.AddField(
            model_name='agentprofile',
            name='training_start_date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='평카인 교육 시작일'),
        ),
    ]
