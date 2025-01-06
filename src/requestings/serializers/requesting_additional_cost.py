from rest_framework import serializers

from requestings.models import RequestingAdditionalCost


class RequestingAdditionalCostSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestingAdditionalCost
        fields = ( 'type', 'name', 'cost', 'image', )
