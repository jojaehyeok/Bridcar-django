from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from vehicles.models import Car

from .evaluation import CarEvaluationResultSerializer
from .carhistory_result import CarhistoryResultSerializer


class CarSerializer(serializers.ModelSerializer):
    evaluation_result = CarEvaluationResultSerializer()
    evaluation_sheets = serializers.SerializerMethodField()
    performance_check_records = serializers.SerializerMethodField()

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_performance_check_records(self, obj):
        return list(map(lambda x: x.file.url, obj.performance_check_records.all()))

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_evaluation_sheets(self, obj):
        return list(map(lambda x: x.image.url, obj.evaluation_sheets.all()))

    class Meta:
        model = Car
        exclude = [ 'requesting_history', 'uuid', ]


class CarSerializerForNotification(serializers.ModelSerializer):
    class Meta:
        model = Car
        exclude = [
            'registration_image', 'instrument_panel_image', 'requesting_history',
            'uuid', 'identification_number_image',
        ]


class DetailCarSerializer(serializers.ModelSerializer):
    evaluation_result = CarEvaluationResultSerializer()
    evaluation_sheets = serializers.SerializerMethodField()
    performance_check_records = serializers.SerializerMethodField()
    carhistory_result = CarhistoryResultSerializer()

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_performance_check_records(self, obj):
        return map(lambda x: x.file.url, obj.performance_check_records.all())

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_evaluation_sheets(self, obj):
        return list(map(lambda x: x.image.url, obj.evaluation_sheets.all()))

    class Meta:
        model = Car
        exclude = [ 'requesting_history', 'uuid', ]
