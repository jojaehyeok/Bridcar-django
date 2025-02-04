# Generated by Django 4.0.6 on 2024-12-04 12:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('requestings', '0029_alter_deliveryregiondivision_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='FinishedDaangnRequestingHistory',
            fields=[
            ],
            options={
                'verbose_name': '완료된 당근마켓 의뢰',
                'verbose_name_plural': '완료된 당근마켓 의뢰목록',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('requestings.requestinghistory',),
        ),
        migrations.CreateModel(
            name='FinishedRequestingHistory',
            fields=[
            ],
            options={
                'verbose_name': '완료된 의뢰',
                'verbose_name_plural': '완료된 의뢰 목록',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('requestings.requestinghistory',),
        ),
    ]
