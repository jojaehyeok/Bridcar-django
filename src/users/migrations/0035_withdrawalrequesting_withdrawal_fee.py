# Generated by Django 4.0.6 on 2023-05-16 05:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0034_alter_agentprofile_user_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='withdrawalrequesting',
            name='withdrawal_fee',
            field=models.PositiveIntegerField(default=0, verbose_name='출금 수수료'),
        ),
    ]
