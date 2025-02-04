# Generated by Django 4.0.6 on 2023-02-20 14:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0011_alter_agentprofile_insurance_expiry_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='balancehistory',
            name='type',
            field=models.CharField(choices=[('manual_deposit', '수동 입금'), ('deposit', '가상계좌 입금'), ('withdrawal', '출금'), ('revenue', '수익금 입금'), ('referer_revenue', '홍보 수익금 입금'), ('fee_escrow', '수수료 에스크로'), ('fee_refund', '수수료 환불')], max_length=32, verbose_name='금액 구분'),
        ),
    ]
