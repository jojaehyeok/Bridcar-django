# Generated by Django 4.0.6 on 2024-11-01 04:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('daangn', '0006_alter_daangnrequestingrequireddocument_key'),
    ]

    operations = [
        migrations.AlterField(
            model_name='daangnrequestingrequireddocument',
            name='description',
            field=models.CharField(max_length=256, verbose_name='서류에 대한 설명'),
        ),
    ]