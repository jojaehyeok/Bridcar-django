from rest_framework import serializers

from phonenumber_field.serializerfields import PhoneNumberField

from drf_spectacular.utils import extend_schema_field

from users.models import Agent
from users.serializers import AgentSerializer

from vehicles.models import Car
from vehicles.serializers import CarSerializer

from requestings.models import RequestingHistory
from requestings.constants import REQUESTING_STATUS
from requestings.serializers import CreateRequestingSerializer, RequestingHistorySerializer
from requestings.utils import get_delivery_cost

from locations.models import CommonLocation
from locations.utils import get_driving_distance_with_kakao

from daangn.models import DaangnRequestingInformation, DaangnRequestingRequiredDocument


class DaangnRequestingRequiredDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DaangnRequestingRequiredDocument
        fields = ( 'key', 'title', 'description', 'is_optional', )


class CreateDaangnRequestingSerializer(CreateRequestingSerializer):
    type = serializers.ChoiceField(choices=[ 'ONLY_DELIVERY', ])
    car_picture = serializers.URLField(required=False)

    dealer_name = serializers.CharField()
    dealer_mobile_number = PhoneNumberField()
    dealer_add_cost = serializers.IntegerField(required=False)

    source_detail_address = serializers.CharField(required=False, allow_blank=True)
    destination_detail_address = serializers.CharField(required=False, allow_blank=True)

    required_documents = DaangnRequestingRequiredDocumentSerializer(
        many=True,
        required=False,
    )

    class Meta:
        model = RequestingHistory
        fields = (
            'car_number', 'car_type', 'car_transmission', 'car_picture', 'type',
            'dealer_name', 'dealer_mobile_number', 'source_address_contact', 'source_road_address',
            'source_detail_address', 'destination_road_address', 'destination_detail_address',
            'dealer_add_cost', 'reservation_date', 'hook_url', 'memo', 'required_documents', 'delivering_cost',
        )

    def create(self, validated_data):
        user = self.context['user']

        source_location = None
        destination_location = None

        requesting_type = validated_data['type']

        try:
            source_location = CommonLocation.objects.create(
                road_address=validated_data['source_road_address'],
                detail_address=validated_data.get('source_detail_address', ''),
                contact=validated_data.get('source_address_contact'),
            )
        except:
            raise serializers.ValidationError({ 'source_road_address': '잘못된 주소입니다.' })

        try:
            destination_location = CommonLocation.objects.create(
                road_address=validated_data['destination_road_address'],
                detail_address=validated_data.get('destination_detail_address', ''),
                contact=validated_data.get('destination_address_contact'),
            )
        except:
            raise serializers.ValidationError({ 'destination_road_address': '잘못된 주소입니다.' })

        #delivering_cost = validated_data.get('delivering_cost', None)
        delivering_cost = get_delivery_cost(validated_data['source_road_address'], validated_data['destination_road_address'])

        if not delivering_cost:
            delivering_cost = None

        new_requesting = RequestingHistory.objects.create(
            client=user,
            status='WAITING_AGENT' if requesting_type != 'ONLY_DELIVERY' else 'WAITING_DELIVERER',
            type=requesting_type,
            source_location=source_location,
            destination_location=destination_location,
            external_client_name=validated_data.get('dealer_name'),
            external_client_mobile_number=validated_data.get('dealer_mobile_number'),
            is_onsite_payment=False,
            reservation_date=validated_data.get('reservation_date', None),
            additional_suggested_cost=validated_data.get('dealer_add_cost', 0),
            hook_url=validated_data.get('hook_url', None),
            memo=validated_data.get('memo', None),
            delivering_cost=delivering_cost,
        )

        new_car = Car(
            requesting_history=new_requesting,
            number=validated_data['car_number'],
            type=validated_data.get('car_type', None),
            transmission=validated_data.get('car_transmission', None),
            classification=validated_data.get('car_classification', None),
            external_car_image_url=validated_data.get('car_picture', None),
        )

        new_car.save()

        daangn_requesting_information = DaangnRequestingInformation.objects.create(
            requesting_history=new_requesting,
            initial_reservation_date=validated_data.get('reservation_date', None),
        )

        required_documents = validated_data.get('required_documents', [])

        for required_document in required_documents:
            DaangnRequestingRequiredDocument.objects.create(
                daangn_requesting_information=daangn_requesting_information,
                **required_document,
            )

        return new_requesting


class DaangnUpdateRequestingSerializer(serializers.ModelSerializer):
    dealer_name = serializers.CharField()
    dealer_mobile_number = PhoneNumberField()

    source_road_address = serializers.CharField()
    source_detail_address = serializers.CharField()
    source_address_contact = serializers.CharField()

    destination_road_address = serializers.CharField()
    destination_detail_address = serializers.CharField()

    memo = serializers.CharField(required=False)

    required_documents = DaangnRequestingRequiredDocumentSerializer(
        many=True,
        required=False,
    )

    class Meta:
        model = RequestingHistory
        fields = (
            'dealer_name', 'dealer_mobile_number', 'source_road_address', 'source_detail_address',
            'source_address_contact', 'destination_road_address', 'destination_detail_address',
            'reservation_date', 'memo', 'required_documents',
        )

    def update(self, instance, validated_data):
        instance.external_client_name = \
            validated_data.get('dealer_name', instance.external_client_name)
        instance.external_client_mobile_number = \
            validated_data.get('dealer_mobile_number', instance.external_client_mobile_number)

        source_location = instance.source_location
        destination_location = instance.destination_location

        source_road_address = \
            validated_data.get('source_road_address', source_location.road_address)

        source_location.destination_address = \
            validated_data.get('source_detail_address', source_location.detail_address)

        need_fetch_source_location_coordinate = False

        if source_road_address != source_location.road_address:
            need_fetch_source_location_coordinate = True
            source_location.road_address = source_road_address

        source_location.save(need_fetch_coordinate=need_fetch_source_location_coordinate)

        destination_road_address = \
            validated_data.get('destination_road_address', destination_location.road_address)

        need_fetch_destination_location_coordinate = False

        destination_location.detail_address = \
            validated_data.get('destination_detail_address', destination_location.detail_address)

        if destination_road_address != destination_location.road_address:
            need_fetch_destination_location_coordinate = True
            destination_location.road_address = destination_road_address

        destination_location.save(need_fetch_coordinate=need_fetch_destination_location_coordinate)

        instance.reservation_date = validated_data.get('reservation_date', instance.reservation_date)
        instance.memo = validated_data.get('memo', instance.memo)

        if need_fetch_source_location_coordinate or need_fetch_destination_location_coordinate:
            instance.delivering_cost = get_delivery_cost(source_road_address, destination_road_address)

        instance.save()

        required_documents = validated_data.get('required_documents', [])

        if len(required_documents) > 0:
            instance.daangn_requesting_information.required_documents.all().delete()

        for required_document in required_documents:
            DaangnRequestingRequiredDocument.objects.create(
                daangn_requesting_information=instance.daangn_requesting_information,
                **required_document,
            )

        return instance


class DaangnRequestingAgentSerializer(AgentSerializer):
    class Meta:
        model = Agent
        fields = ( 'name', 'mobile_number', )


class DaangnRequestingCarSerializer(CarSerializer):
    picture = serializers.SerializerMethodField()

    class Meta:
        model = Car
        fields = ( 'number', 'type', 'transmission', 'picture', )

    @extend_schema_field(serializers.URLField())
    def get_picture(self, obj):
        return obj.external_car_image_url


class DaangnRequestingDetailSerializer(RequestingHistorySerializer):
    car = DaangnRequestingCarSerializer()

    dealer_name = serializers.SerializerMethodField()
    dealer_mobile_number = serializers.SerializerMethodField()

    #agent = DaangnRequestingAgentSerializer()
    deliverer = DaangnRequestingAgentSerializer()

    is_paid = serializers.SerializerMethodField()
    is_require_refund = serializers.SerializerMethodField()

    class Meta:
        model = RequestingHistory
        fields = (
            'id', 'car', 'type', 'dealer_name', 'dealer_mobile_number', 'source_location',
            'destination_location', 'inspection_cost', 'delivering_cost', 'reservation_date',
            'status', 'deliverer', 'hook_url', 'memo', 'created_at', 'is_paid',
            'delivery_result', 'estimated_service_date', 'is_require_refund',
        )

    @extend_schema_field(serializers.CharField())
    def get_dealer_name(self, obj):
        return obj.external_client_name

    @extend_schema_field(PhoneNumberField)
    def get_dealer_mobile_number(self, obj):
        return str(obj.external_client_mobile_number)

    @extend_schema_field(serializers.BooleanField())
    def get_is_paid(self, obj):
        return obj.daangn_requesting_information.is_paid

    @extend_schema_field(serializers.BooleanField())
    def get_is_require_refund(self, obj):
        requesting_status = dict(REQUESTING_STATUS)

        if obj.deliverer is not None and obj.has_agent_delivery_start:
            return True

        return False

    @extend_schema_field(serializers.IntegerField())
    def get_delivering_cost(self, obj):
        if obj.delivering_cost is None:
            return None

        return obj.delivering_cost + (obj.stopovers.count() * 5000)
