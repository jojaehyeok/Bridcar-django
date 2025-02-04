# Generated by Django 4.0.6 on 2023-02-03 14:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_dealerprofile_business_items_alter_user_created_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='balancehistory',
            name='type',
            field=models.CharField(choices=[('manual_deposit', '수동 입금'), ('deposit', '가상계좌 입금'), ('withdrawal', '출금'), ('revenue', '수익금 입금'), ('referer_revenue', '홍보 수익금 입금'), ('fee_escrow', '수수료 에스크로')], max_length=32, verbose_name='금액 구분'),
        ),
    ]
