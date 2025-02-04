# Generated by Django 4.0.6 on 2023-01-30 15:54

from django.db import migrations
import multiselectfield.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_dealerprofile_business_categories'),
    ]

    operations = [
        migrations.AddField(
            model_name='agentprofile',
            name='activity_area',
            field=multiselectfield.db.fields.MultiSelectField(blank=True, choices=[('평카', '평카'), ('평카탁송', '평카탁송'), ('검수탁송', '검수탁송'), ('일반탁송', '일반탁송'), ('홍보 (영업)', '홍보 (영업)'), ('기타', '기타')], max_length=32, null=True, verbose_name='활동영역'),
        ),
    ]
