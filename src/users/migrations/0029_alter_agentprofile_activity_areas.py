# Generated by Django 4.0.6 on 2023-03-15 09:32

from django.db import migrations
import multiselectfield.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0028_agentprofile_affiliated_area_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='agentprofile',
            name='activity_areas',
            field=multiselectfield.db.fields.MultiSelectField(blank=True, choices=[('zero 평가인', 'zero 평가인'), ('평가', '평가'), ('평카탁송', '평가탁송'), ('검수탁송', '검수탁송'), ('일반탁송', '일반탁송'), ('홍보 (영업)', '홍보 (영업)'), ('기타', '기타')], max_length=128, null=True, verbose_name='활동 현황'),
        ),
    ]
