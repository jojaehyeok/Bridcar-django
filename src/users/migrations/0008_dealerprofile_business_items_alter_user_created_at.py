# Generated by Django 4.0.6 on 2023-02-01 14:33

from django.db import migrations, models
import multiselectfield.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_rename_activity_area_agentprofile_activity_areas'),
    ]

    operations = [
        migrations.AddField(
            model_name='dealerprofile',
            name='business_items',
            field=multiselectfield.db.fields.MultiSelectField(blank=True, choices=[('평가', '평가'), ('검수', '검수'), ('탁송', '탁송'), ('중개', '중개')], max_length=32, null=True, verbose_name='회사 아이템'),
        ),
        migrations.AlterField(
            model_name='user',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='가입 일자'),
        ),
    ]
