# Generated by Django 4.0.6 on 2022-09-19 13:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('requestings', '0002_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='bulkrequesting',
            options={'verbose_name': '다량 발주 신청 내역', 'verbose_name_plural': '다량 발주 신청 내역 목록'},
        ),
    ]