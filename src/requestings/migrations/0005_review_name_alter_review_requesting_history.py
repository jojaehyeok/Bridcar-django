# Generated by Django 4.0.6 on 2022-11-23 10:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('requestings', '0004_review_is_exposing_to_dealer'),
    ]

    operations = [
        migrations.AddField(
            model_name='review',
            name='name',
            field=models.CharField(blank=True, max_length=32, null=True, verbose_name='필수 아님 (의뢰로 등록된 경우 의뢰자 이름 우선)'),
        ),
        migrations.AlterField(
            model_name='review',
            name='requesting_history',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='review', to='requestings.requestinghistory', verbose_name='대상 의뢰'),
        ),
    ]
