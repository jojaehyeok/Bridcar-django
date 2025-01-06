from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from users.models import User
from users.constants import TOSS_PAYMENTS_VIRTUAL_ACCOUNT_BANKS


class IssueTokenSerializer(serializers.Serializer):
    api_id = serializers.CharField()
    api_secret = serializers.CharField()
    role = serializers.ChoiceField(choices=('api', 'api'))

    class Meta:
        model = User
        fields = ( 'api_id', 'api_secret', 'role', )


class IssuedTokenResultSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
