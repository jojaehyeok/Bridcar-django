# Generated by Django 4.0.6 on 2023-03-15 09:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0029_alter_agentprofile_activity_areas'),
    ]

    operations = [
        migrations.AddField(
            model_name='agentprofile',
            name='first_working_start_date',
            field=models.DateField(blank=True, null=True, verbose_name='최초 근무 시작일'),
        ),
    ]