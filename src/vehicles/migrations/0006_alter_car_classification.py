# Generated by Django 4.0.6 on 2023-01-24 14:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vehicles', '0005_alter_carhistoryresult_scrapping_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='car',
            name='classification',
            field=models.CharField(blank=True, choices=[('승용차', '승용차'), ('대형', '대형'), ('화물', '화물'), ('렉카', '렉카'), ('추레라', '추레라'), ('캠핑카', '캠핑카')], max_length=10, null=True, verbose_name='차량 분류'),
        ),
    ]
