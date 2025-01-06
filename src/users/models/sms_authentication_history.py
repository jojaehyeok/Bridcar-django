from django.db import models

from phonenumber_field.modelfields import PhoneNumberField

from users.models import User
from users.constants import SMS_AUTHENTICATION_PURPOSES


class SMSAuthenticationHistory(models.Model):
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='인증 요청 시각',
    )

    mobile_number = PhoneNumberField(
        verbose_name='핸드폰 번호'
    )

    purpose = models.CharField(
        max_length=32,
        choices=SMS_AUTHENTICATION_PURPOSES,
        verbose_name='본인인증 목적',
    )

    authentication_code = models.CharField(
        max_length=10,
        verbose_name='인증번호',
    )

    without_alimtalk = models.BooleanField(
        default=False,
        verbose_name='알림톡 미발송 여부',
    )

    class Meta:
        db_table = 'sms_authentication_histories'
        verbose_name = '문자인증 요청'
        verbose_name_plural = '문자인증 요청 내역'

    def save(self, **kwargs):
        if not self.pk:
            from notifications.utils import KakaoAlimtalkSender

            if self.without_alimtalk == False:
                KakaoAlimtalkSender(
                    'AUTHENTICATION_CODE',
                    receivers=[ str(self.mobile_number), ],
                    parameters={ 'authentication_code': str(self.authentication_code), },
                ).start()

        super(SMSAuthenticationHistory, self).save(**kwargs)
