# Generated by Django 4.0.6 on 2023-02-01 15:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('requestings', '0007_deliveryregiondivision_deliveryfeerelation'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='deliveryregiondivision',
            name='dong_list',
        ),
        migrations.AddField(
            model_name='deliveryregiondivision',
            name='gu_dong_list',
            field=models.TextField(default='', verbose_name='소속 구, 동 리스트 (개행으로 구분)'),
            preserve_default=False,
        ),
    ]