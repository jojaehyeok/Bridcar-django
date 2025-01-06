from rest_framework import serializers

from drf_spectacular.utils import extend_schema_field

from requestings.models import BulkRequesting


class UploadBulkRequestingSerializer(serializers.ModelSerializer):
    class Meta:
        model = BulkRequesting
        fields = ( 'file', )

    def create(self, validated_data):
        client = self.context['client']

        return BulkRequesting.objects.create(
            client=client,
            **validated_data,
        )
