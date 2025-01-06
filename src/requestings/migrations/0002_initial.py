# Generated by Django 4.0.6 on 2022-09-15 15:33

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('locations', '0001_initial'),
        ('users', '0001_initial'),
        ('requestings', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='requestingsettlement',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='settlements', to=settings.AUTH_USER_MODEL, verbose_name='정산 대상 평카인'),
        ),
        migrations.AddField(
            model_name='requestinghistory',
            name='agent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='allocation_requestings', to='users.agent', verbose_name='담당 평카인'),
        ),
        migrations.AddField(
            model_name='requestinghistory',
            name='client',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='requestings', to='users.dealer', verbose_name='의뢰인'),
        ),
        migrations.AddField(
            model_name='requestinghistory',
            name='deliverer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='allocation_as_deliverer_requestings', to='users.agent', verbose_name='담당 탁송기사'),
        ),
        migrations.AddField(
            model_name='requestinghistory',
            name='destination_location',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='requestings_used_as_destination', to='locations.commonlocation', verbose_name='도착지 위치'),
        ),
        migrations.AddField(
            model_name='requestinghistory',
            name='fee_payment_histories',
            field=models.ManyToManyField(blank=True, null=True, related_name='fee_payment_histories', to='users.balancehistory', verbose_name='평카인 수수료 결제 기록'),
        ),
        migrations.AddField(
            model_name='requestinghistory',
            name='source_location',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='requestings_used_as_source', to='locations.commonlocation', verbose_name='출발지 위치'),
        ),
        migrations.AddField(
            model_name='requestinghistory',
            name='stopovers',
            field=models.ManyToManyField(blank=True, null=True, related_name='requestings_used_as_stopover', to='locations.commonlocation', verbose_name='경유지'),
        ),
        migrations.AddField(
            model_name='requestingchattingmessage',
            name='read_users',
            field=models.ManyToManyField(related_name='read_requesting_messages', to=settings.AUTH_USER_MODEL, verbose_name='읽은 사람'),
        ),
        migrations.AddField(
            model_name='requestingchattingmessage',
            name='requesting_history',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chatting_messages', to='requestings.requestinghistory', verbose_name='대상 의뢰'),
        ),
        migrations.AddField(
            model_name='requestingchattingmessage',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='requesting_chatting_messages', to=settings.AUTH_USER_MODEL, verbose_name='작성한 유저'),
        ),
        migrations.AddField(
            model_name='requestingadditionalcost',
            name='requesting_history',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='additional_costs', to='requestings.requestinghistory', verbose_name='대상 의뢰'),
        ),
        migrations.AddField(
            model_name='deliveryresult',
            name='requesting_history',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='delivery_result', to='requestings.requestinghistory', verbose_name='대상 의뢰'),
        ),
        migrations.AddField(
            model_name='carbasicimage',
            name='delivery_result',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='car_basic_images', to='requestings.deliveryresult', verbose_name='기본 사진 목록'),
        ),
        migrations.AddField(
            model_name='caraccidentsiteimage',
            name='delivery_result',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='car_accident_site_images', to='requestings.deliveryresult', verbose_name='대상 탁송 결과'),
        ),
        migrations.AddField(
            model_name='bulkrequesting',
            name='client',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bulk_requestings', to='users.dealer', verbose_name='대상 딜러'),
        ),
    ]