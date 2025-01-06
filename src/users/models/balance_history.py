from functools import reduce

from django.db import models

from users.constants import BALANCE_HISTORY_TYPE, BALANCE_HISTORY_SUB_TYPES

from .user import Agent


class BalanceHistory(models.Model):
    user = models.ForeignKey(
        Agent,
        on_delete=models.CASCADE,
        related_name='balance_histories',
        verbose_name='대상 유저',
    )

    transaction_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='거래 시각',
    )

    type = models.CharField(
        max_length=32,
        choices=BALANCE_HISTORY_TYPE,
        verbose_name='금액 구분',
    )

    sub_type = models.CharField(
        max_length=32,
        verbose_name='금액 세부 구분',
        choices=BALANCE_HISTORY_SUB_TYPES,
        null=True,
        blank=True,
    )

    amount = models.PositiveIntegerField(
        verbose_name='금액',
    )

    acc_amount = models.PositiveIntegerField(
        default=0,
        verbose_name='누적 금액',
    )

    class Meta:
        db_table = 'balance_histories'
        verbose_name = '계좌 사용 내역'
        verbose_name_plural = '계좌 사용 내역 목록'

    def __str__(self):
        return f'{ self.user.name } ({ int(self.amount) }원)'

    def save(self, *args, **kwargs):
        user = self.user

        withdrawal_processing_amounts = reduce(
            lambda acc, x: acc + x.amount,
            list(user.withdrawal_requestings.filter(is_processed=False)),
            0
        )

        if self.pk == None and self.type == 'fee_escrow':
            user.agent_profile.balance -= (self.amount + withdrawal_processing_amounts)
            user.agent_profile.save()

            self.acc_amount = user.agent_profile.balance
        elif self.type == 'withdrawal':
            user.agent_profile.balance -= self.amount
            user.agent_profile.save()

            self.acc_amount = user.agent_profile.balance + withdrawal_processing_amounts
        else:
            user.agent_profile.balance += self.amount
            user.agent_profile.save()

            self.acc_amount = user.agent_profile.balance + withdrawal_processing_amounts

        super(BalanceHistory, self).save(*args, **kwargs)

    def refund_fee(self):
        user = self.user

        if user.is_agent and self.type == 'fee_escrow':
            BalanceHistory.objects.create(
                user=self.user,
                type='fee_refund',
                amount=self.amount,
            )

            self.delete()
