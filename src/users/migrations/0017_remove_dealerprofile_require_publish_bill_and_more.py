# Generated by Django 4.0.6 on 2023-02-23 15:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0016_alter_dealerprofile_company'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dealerprofile',
            name='require_publish_bill',
        ),
        migrations.AddField(
            model_name='dealercompany',
            name='require_publish_bill',
            field=models.BooleanField(default=True, verbose_name='계산서 발행유무'),
        ),
    ]
