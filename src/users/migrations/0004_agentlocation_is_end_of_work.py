# Generated by Django 4.0.6 on 2022-11-26 17:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_smsauthenticationhistory_without_alimtalk'),
    ]

    operations = [
        migrations.AddField(
            model_name='agentlocation',
            name='is_end_of_work',
            field=models.BooleanField(default=False, verbose_name='업무 종료 여부'),
        ),
    ]
