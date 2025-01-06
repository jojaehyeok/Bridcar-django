from rest_framework import serializers
from rest_framework.exceptions import ParseError

from drf_spectacular.utils import extend_schema_field

from vehicles.models import CarEvaluationSheet

from users.serializers import UserSerializer

from requestings.models import RequestingChattingMessage


class RequestingChattingMessageSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = RequestingChattingMessage
        fields = ( 'id', 'user', 'created_at', 'text', 'image', )


class WriteRequestingChattingMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestingChattingMessage
        fields = ( 'sending_to', 'text', 'image', )

    def save(self, **kwargs):
        user = kwargs.get('user')
        requesting_history = kwargs.get('requesting_history')

        sending_to = self.validated_data.pop('sending_to')

        if user == requesting_history.agent or user == requesting_history.deliverer:
            sending_to = 'client'

        if user == requesting_history.client and sending_to == 'client':
            raise ParseError('INVALID_SENDING_TO')

        return RequestingChattingMessage.objects.create(
            user=user,
            requesting_history=requesting_history,
            sending_to=sending_to,
            **self.validated_data,
        )
