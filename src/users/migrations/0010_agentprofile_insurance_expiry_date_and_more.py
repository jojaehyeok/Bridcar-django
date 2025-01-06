# Generated by Django 4.0.6 on 2023-02-19 12:11

from django.db import migrations, models
import multiselectfield.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0009_alter_balancehistory_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='agentprofile',
            name='insurance_expiry_date',
            field=models.DateField(blank=True, null=True, verbose_name='보험 만료 일시'),
        ),
        migrations.AlterField(
            model_name='dealerprofile',
            name='business_categories',
            field=multiselectfield.db.fields.MultiSelectField(blank=True, choices=[('중고차 매매업', '중고차 매매업'), ('신차매매업', '신차매매업'), ('중고차딜러', '중고차딜러'), ('신차딜러', '신차딜러'), ('렌트카', '렌트카'), ('선물사 (리스, 채권)', '선물사 (리스, 채권)'), ('수출', '수출'), ('기타', '기타')], max_length=32, null=True, verbose_name='사업분류'),
        ),
    ]