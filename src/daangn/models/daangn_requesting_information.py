from django.db import models


class DaangnRequestingInformation(models.Model):
    requesting_history = models.OneToOneField(
        'requestings.RequestingHistory',
        on_delete=models.CASCADE,
        related_name='daangn_requesting_information',
        verbose_name='대상 의뢰',
    )

    initial_reservation_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='최초 예약 시간',
    )

    is_paid = models.BooleanField(
        default=False,
        verbose_name='입금 여부 (확정 여부)',
    )

    is_forced_exposure = models.BooleanField(
        default=False,
        verbose_name='확정 무관 강제 노출 여부',
    )

    def __str__(self):
        return f'{ self.requesting_history.id }번 당근의뢰 추가 정보'

    class Meta:
        db_table = 'daangn_requesting_informations'
        verbose_name = '당근 의뢰 추가 정보'
        verbose_name_plural = '당근 의뢰 추가 정보 목록'
