# Generated by Django 4.0.6 on 2023-03-29 16:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('requestings', '0014_deliveryregiondivision_exclude_gu_dong_list'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='deliveryregiondivision',
            name='exclude_gu_dong_list',
        ),
    ]