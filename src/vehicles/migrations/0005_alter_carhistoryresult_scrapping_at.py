# Generated by Django 4.0.6 on 2022-11-27 08:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vehicles', '0004_rename_abnormal_while_driving_carevaluationresult_abnormal_while_driving_memo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='carhistoryresult',
            name='scrapping_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='스크래핑 한 시각'),
        ),
    ]
