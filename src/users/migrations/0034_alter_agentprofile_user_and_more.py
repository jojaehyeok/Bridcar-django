# Generated by Django 4.0.6 on 2023-03-20 16:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0033_rename_referer_reward_rate_agentprofile_referer_revenue_rate'),
    ]

    operations = [
        migrations.AlterField(
            model_name='agentprofile',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='agent_profile', to='users.agent', verbose_name='회원이름'),
        ),
        migrations.AlterField(
            model_name='dealercompany',
            name='cooperation_level',
            field=models.CharField(blank=True, max_length=128, null=True, verbose_name='협력도'),
        ),
        migrations.AlterField(
            model_name='dealercompany',
            name='settlement_date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='정산일'),
        ),
    ]
