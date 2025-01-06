from rest_framework import serializers

from vehicles.models import PerformanceCheckRecord


class UpdatePerformanceCheckRecordsSerializer(serializers.Serializer):
    files = serializers.ListField(child=serializers.FileField())

    def create(self, validated_data):
        files = validated_data.get('files', [])

        last_created_object = None

        for file in files:
            last_created_object = PerformanceCheckRecord.objects.create(
                car=self.context['car'],
                file=file,
            )

        return last_created_object
