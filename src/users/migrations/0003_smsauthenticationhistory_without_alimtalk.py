# Generated by Django 4.0.6 on 2022-09-19 12:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_user_is_test_account'),
    ]

    operations = [
        migrations.AddField(
            model_name='smsauthenticationhistory',
            name='without_alimtalk',
            field=models.BooleanField(default=False, verbose_name='알림톡 미발송 여부'),
        ),
    ]
