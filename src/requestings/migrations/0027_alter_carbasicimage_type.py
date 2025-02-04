# Generated by Django 4.0.6 on 2024-11-16 03:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('requestings', '0026_alter_carbasicimage_sub_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='carbasicimage',
            name='type',
            field=models.CharField(choices=[('CAR_KEY', '차키'), ('DASHBOARD', '계기판'), ('EXTERIOR', '외장'), ('INTERIOR', '내장'), ('WHEEL', '휠'), ('DAMAGED_PARTS', '사고 부위'), ('REQUIRED_DOCUMENTS', '명의이전 구비서류'), ('ETC', '기타')], default='EXTERIOR', max_length=128, verbose_name='사진 구분'),
        ),
    ]
