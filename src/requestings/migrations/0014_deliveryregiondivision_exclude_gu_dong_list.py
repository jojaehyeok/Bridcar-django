# Generated by Django 4.0.6 on 2023-03-29 16:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('requestings', '0013_alter_requestingadditionalcost_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='deliveryregiondivision',
            name='exclude_gu_dong_list',
            field=models.TextField(blank=True, null=True, verbose_name='제외할 소속 구, 법정동 리스트 (개행으로 구분)'),
        ),
    ]
