from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from users.models import TossVirtualAccount


class TossVirtualAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = TossVirtualAccount
        exclude = [ 'id', ]
