from rest_framework import serializers
from rest_framework.exceptions import ParseError, PermissionDenied

from users.models import WithdrawalRequesting


class WithdrawlRequestingSerializer(serializers.ModelSerializer):
    class Meta:
        model = WithdrawalRequesting
        fields = [ 'requested_at', 'amount', ]


class RequestWithdrawalSerializer(serializers.ModelSerializer):
    class Meta:
        model = WithdrawalRequesting
        fields = [ 'amount', ]

    def validate(self, data):
        agent = self.context['agent']

        if agent.agent_profile.balance < data['amount']:
            raise PermissionDenied('NOT_ENOUGH_BALANCE')

        if data['amount'] <= 30000:
            raise ParseError('CANNOT_WITHDRAWAL_WITH_THIS_AMOUNT')

        return data

    def create(self, validated_data):
        agent = self.context['agent']
        amount = validated_data['amount']

        return WithdrawalRequesting.objects.create(
            agent=agent,
            amount=amount,
        )
