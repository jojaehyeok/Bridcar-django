# Generated by Django 4.0.6 on 2023-02-22 12:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0014_dealercompany_uuid'),
    ]

    operations = [
        migrations.RenameField(
            model_name='dealercompany',
            old_name='company_name',
            new_name='name',
        ),
        migrations.AlterField(
            model_name='dealercompany',
            name='business_registration_number',
            field=models.CharField(default='11111', max_length=100, verbose_name='사업자 등록번호'),
            preserve_default=False,
        ),
    ]
