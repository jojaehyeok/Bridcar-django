from rest_framework import serializers

from drf_spectacular.utils import extend_schema_field

from locations.models import CommonLocation

from locations.utils import pointFieldToCoord


class CoordSerializer(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()


class DrivingRouteSerializer(serializers.Serializer):
    distance = serializers.FloatField()
    distance_to_source = serializers.FloatField()


class CommonLocationSerializer(serializers.ModelSerializer):
    coord = serializers.SerializerMethodField()

    class Meta:
        model = CommonLocation
        fields = '__all__'

    @extend_schema_field(CoordSerializer())
    def get_coord(self, obj):
        return pointFieldToCoord(obj.coord)
