from rest_framework import serializers

from drf_spectacular.utils import extend_schema_field

from vehicles.models import CarEvaluationSheet

from users.serializers import UserSerializer

from requestings.models import RequestingHistory


class ConfirmRequestingEvaluationSerializer(serializers.Serializer):
    need_delivery = serializers.BooleanField(
        required=True,
        help_text='매입 유무',
    )

    class Meta:
        fields = ( 'need_delivery', )
