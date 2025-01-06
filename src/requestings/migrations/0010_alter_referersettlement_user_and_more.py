# Generated by Django 4.0.6 on 2023-02-06 17:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0009_alter_balancehistory_type'),
        ('requestings', '0009_alter_deliveryregiondivision_gu_dong_list_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='referersettlement',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='referer_settlements', to='users.agent', verbose_name='정산 대상 평카인'),
        ),
        migrations.AlterField(
            model_name='requestingsettlement',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='settlements', to='users.agent', verbose_name='정산 대상 평카인'),
        ),
    ]