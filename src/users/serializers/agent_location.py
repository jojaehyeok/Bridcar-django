from django.contrib.gis.geos.geometry import GEOSGeometry

from rest_framework import serializers
from rest_framework.exceptions import ParseError

from drf_spectacular.utils import extend_schema_field

from users.models import AgentLocation

from locations.utils import search_road_address_from_kakao

from locations.utils import pointFieldToCoord


class LocationCoordSerializer(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()


class AgentLocationSerializer(serializers.ModelSerializer):
    coord = serializers.SerializerMethodField()
    manual_coord = serializers.SerializerMethodField()

    class Meta:
        model = AgentLocation
        fields = '__all__'

    @extend_schema_field(LocationCoordSerializer())
    def get_coord(self, obj):
        return pointFieldToCoord(obj.coord)

    @extend_schema_field(LocationCoordSerializer())
    def get_manual_coord(self, obj):
        return pointFieldToCoord(obj.manual_coord)


class AgentCurrentLocationSerializer(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()

    class Meta:
        model = AgentLocation
        fields = [ 'latitude', 'longitude', ]


class AgentLocationConfigSerializer(serializers.ModelSerializer):
    using_auto_dispatch = serializers.BooleanField(required=False)
    using_manual_address = serializers.BooleanField(required=False)

    class Meta:
        model = AgentLocation
        fields = [
            'manual_road_address', 'using_auto_dispatch', \
            'desired_destination_address', 'using_manual_address'
        ]

    def validate(self, data):
        manual_road_address = data.get('manual_road_address', None)

        if manual_road_address != None:
            try:
                address_search_result = search_road_address_from_kakao(manual_road_address)
                lng, lat = float(address_search_result['x']), float(address_search_result['y'])

                data['manual_coord'] = GEOSGeometry(f'POINT({ lat } { lng })', srid=4326)
            except:
                raise ParseError('INVALID_MANUAL_ROAD_ADDRESS')

        return data

    def update(self, obj, validated_data):
        using_auto_dispatch = validated_data.get('using_auto_dispatch', None)
        manual_road_address = validated_data.get('manual_road_address', None)
        manual_coord = validated_data.get('manual_coord', None)
        desired_destination_address = validated_data.get('desired_destination_address', None)
        using_manual_address = validated_data.get('using_manual_address', None)

        if manual_road_address and manual_coord:
            obj.manual_road_address = manual_road_address
            obj.manual_coord = manual_coord
            obj.using_manual_address = True

        if using_manual_address == False and obj.using_manual_address:
            obj.manaul_coord = None
            obj.manual_road_address = None
            obj.using_manual_address = False

        obj.desired_destination_address = desired_destination_address

        if using_auto_dispatch != None:
            obj.using_auto_dispatch = using_auto_dispatch

        obj.save()

        return obj
