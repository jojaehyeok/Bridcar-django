from django.db import models

from phonenumber_field.modelfields import PhoneNumberField

from users.models import Agent
from users.constants import SMS_AUTHENTICATION_PURPOSES


class WithdrawalRequesting(models.Model):
    agent = models.ForeignKey(
        Agent,
        on_delete=models.CASCADE,
        related_name='withdrawal_requestings',
        verbose_name='대상 평카인',
    )

    requested_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='출금 신청 시각',
    )

    amount = models.PositiveIntegerField(
        verbose_name='출금 요청 금액',
    )

    withdrawal_fee = models.PositiveIntegerField(
        default=0,
        verbose_name='출금 수수료',
    )

    is_processed = models.BooleanField(
        default=False,
        verbose_name='출금 처리 여부',
    )

    class Meta:
        db_table = 'withdrawal_requestings'
        verbose_name = '출금 요청'
        verbose_name_plural = '출금 요청 목록'

    def save(self, **kwargs):
        if self.pk == None:
            self.agent.agent_profile.balance -= self.amount
            self.agent.agent_profile.save()

        super(WithdrawalRequesting, self).save(**kwargs)
