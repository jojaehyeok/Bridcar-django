from rest_framework import serializers

from drf_spectacular.utils import extend_schema_field

from users.serializers import UserSerializer

from requestings.models import RequestingSettlement


class RequestingSettlementSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = RequestingSettlement
