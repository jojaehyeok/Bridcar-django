import uuid

from django.db import models

from users.models import User
from users.constants import SMS_AUTHENTICATION_PURPOSES
from users.utils import request_toss_payments_virtual_account


class TossVirtualAccount(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='toss_virtual_accounts',
        verbose_name='소유한 유저',
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='계좌 생성 시각',
    )

    expired_at = models.DateTimeField(
        verbose_name='계좌 만료 시각',
    )

    order_id = models.CharField(
        unique=True,
        max_length=128,
        verbose_name='오더 ID',
    )

    secret = models.CharField(
        max_length=128,
        verbose_name='TOSS 결제 시크릿 키'
    )

    amount = models.PositiveIntegerField(
        verbose_name='입금 금액',
        default=0,
    )

    bank = models.CharField(
        max_length=32,
        verbose_name='입금 은행',
    )

    account_number = models.CharField(
        max_length=128,
        verbose_name='입금 계좌번호'
    )

    is_deposited = models.BooleanField(
        default=False,
        verbose_name='입금 완료 여부',
    )

    class Meta:
        db_table = 'toss_virtual_accounts'
        verbose_name = '토스 가상계좌'
        verbose_name_plural = '토스 가상계좌 목록'

    def save(self, **kwargs):
        self.order_id = uuid.uuid4()

        result = request_toss_payments_virtual_account(
            order_id=self.order_id,
            amount=self.amount,
            bank=self.bank,
            user=self.user,
        )

        self.secret, self.account_number, self.expired_at = result

        super(TossVirtualAccount, self).save(**kwargs)
