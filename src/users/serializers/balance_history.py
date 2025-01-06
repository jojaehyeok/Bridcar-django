from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from users.models import BalanceHistory
from users.constants import TOSS_PAYMENTS_VIRTUAL_ACCOUNT_BANKS


class RequestDepositSerializer(serializers.Serializer):
    amount = serializers.IntegerField()
    bank = serializers.ChoiceField(
        choices=TOSS_PAYMENTS_VIRTUAL_ACCOUNT_BANKS
    )

    class Meta:
        model = BalanceHistory
        fields = [ 'amount', 'bank', ]


class BalanceHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BalanceHistory
        exclude = [ 'user', ]


class UpdateDepositResultSerializer(serializers.Serializer):
    createdAt = serializers.DateTimeField()
    secret = serializers.CharField()
    status = serializers.CharField()
    transactionKey = serializers.CharField()
    orderId = serializers.CharField()
