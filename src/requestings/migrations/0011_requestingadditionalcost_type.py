# Generated by Django 4.0.6 on 2023-02-19 16:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('requestings', '0010_alter_referersettlement_user_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='requestingadditionalcost',
            name='type',
            field=models.CharField(choices=[('주유비', '주유비'), ('기타', '기타')], default='기타', max_length=32, verbose_name='요금 구분'),
        ),
    ]
