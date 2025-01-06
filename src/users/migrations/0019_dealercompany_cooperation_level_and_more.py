# Generated by Django 4.0.6 on 2023-03-11 15:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0018_agentprofile_ability_to_acquire_education_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='dealercompany',
            name='cooperation_level',
            field=models.CharField(blank=True, max_length=128, null=True, verbose_name='협력도 (개인)'),
        ),
        migrations.AddField(
            model_name='dealercompany',
            name='settlement_date',
            field=models.DateTimeField(blank=True, help_text='회사 소속의 회원일 경우 공란', null=True, verbose_name='정산일 (개인)'),
        ),
        migrations.AddField(
            model_name='dealerprofile',
            name='cooperation_level',
            field=models.CharField(blank=True, max_length=128, null=True, verbose_name='협력도 (개인)'),
        ),
        migrations.AddField(
            model_name='dealerprofile',
            name='settlement_date',
            field=models.DateTimeField(blank=True, help_text='회사 소속의 회원일 경우 공란', null=True, verbose_name='정산일 (개인)'),
        ),
        migrations.AlterField(
            model_name='agentprofile',
            name='total_delivery_count',
            field=models.PositiveIntegerField(default=0, verbose_name='총 탁송 횟수'),
        ),
        migrations.AlterField(
            model_name='agentprofile',
            name='total_evaluation_count',
            field=models.PositiveIntegerField(default=0, verbose_name='총 평가 횟수'),
        ),
        migrations.AlterField(
            model_name='agentprofile',
            name='total_inspection_count',
            field=models.PositiveIntegerField(default=0, verbose_name='총 검수 횟수'),
        ),
        migrations.AlterField(
            model_name='agentprofile',
            name='total_marketing_count',
            field=models.PositiveIntegerField(default=0, verbose_name='총 홍보 횟수'),
        ),
    ]
