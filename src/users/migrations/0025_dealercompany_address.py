# Generated by Django 4.0.6 on 2023-03-12 16:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0024_dealercompany_business_opening_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='dealercompany',
            name='address',
            field=models.CharField(blank=True, max_length=128, null=True, verbose_name='주소'),
        ),
    ]
