# Generated by Django 4.0.6 on 2022-09-15 15:33

from django.db import migrations, models
import multiselectfield.db.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', multiselectfield.db.fields.MultiSelectField(choices=[('USER', '일반 유저 알림'), ('CONTROL_ROOM', '상황실 전용 알림')], max_length=32, verbose_name='알림 구분')),
                ('subject', models.CharField(choices=[('CREATE_REQUESTING', '오더 신청'), ('CREATE_BULK_REQUESTING', '대량 오더 신청'), ('START_EVALUATION', '평카(검수) 시작'), ('FINISH_EVALUATION', '평카(검수) 종료'), ('CLIENT_PURCHASE_DECISION', '의뢰인 매입결정 결과'), ('DEPARTURE_DELIVERY', '탁송 시작'), ('ARRIVAL_DELIVERY', '탁송 완료'), ('CLIENT_CONFIRM_ARRIVAL_DELIVERY', '의뢰인 인도 확인'), ('REQUESTING_CHATTING', '의뢰 채팅')], max_length=32, verbose_name='알림 주제')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='알림 생성 시각')),
                ('data', models.CharField(blank=True, max_length=100, null=True, verbose_name='추가 데이터')),
                ('is_read', models.BooleanField(default=False, verbose_name='알림 읽음 여부')),
            ],
            options={
                'verbose_name': '알림',
                'verbose_name_plural': '알림 목록',
                'db_table': 'notifications',
            },
        ),
    ]