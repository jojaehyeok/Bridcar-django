import json
import pyproj

from functools import reduce

from django.db.models import Q
from django.utils import timezone

from rest_framework import serializers

from drf_spectacular.utils import extend_schema_field

from vehicles.models import Car, CarEvaluationSheet
from vehicles.serializers import CarSerializer, DetailCarSerializer, CarSerializerForNotification

from users.serializers import UserSerializer, UserForNotificationSerializer

from locations.models import CommonLocation
from locations.serializers import CommonLocationSerializer, DrivingRouteSerializer
from locations.utils import get_driving_distance_with_kakao

from requestings.models import RequestingHistory

from daangn.models import DaangnRequestingInformation, DaangnRequestingRequiredDocument

from .requesting_additional_cost import RequestingAdditionalCostSerializer
from .delivery_result import DeliveryResultSerializer
from .review import ReviewSerializer


class RequestingHistoryCommonSerializer(serializers.Serializer):
    stopovers = serializers.SerializerMethodField()
    driving_route = serializers.SerializerMethodField()

    @extend_schema_field(CommonLocationSerializer(many=True))
    def get_stopovers(self, obj):
        return CommonLocationSerializer(obj.stopovers.all(), many=True).data

    @extend_schema_field(DrivingRouteSerializer())
    def get_driving_route(self, obj):
        user = self.context.get('user', None)

        if not user or not hasattr(user, 'agent_location'):
            return None

        if not obj.source_location or not obj.destination_location:
            return { 'distance': obj.distance_between_source_destination, 'distance_to_source': 0, }

        geod = pyproj.Geod(ellps='WGS84')
        _, _, distance_to_source = geod.inv(
            user.agent_location.coord[0],
            user.agent_location.coord[1],
            obj.source_location.coord[0],
            obj.source_location.coord[1],
        )

        return { 'distance': obj.distance_between_source_destination, 'distance_to_source': round(distance_to_source / 1000, 1), }


class RequestingHistorySerializerForNotification(serializers.ModelSerializer):
    car = CarSerializerForNotification(read_only=True)
    source_location = CommonLocationSerializer()
    destination_location = CommonLocationSerializer()

    stopovers = serializers.SerializerMethodField()
    total_cost = serializers.SerializerMethodField()

    class Meta:
        model = RequestingHistory
        exclude = ( 'client', 'agent', 'deliverer', )

    @extend_schema_field(CommonLocationSerializer(many=True))
    def get_stopovers(self, obj):
        return CommonLocationSerializer(obj.stopovers.all(), many=True).data

    @extend_schema_field(serializers.IntegerField())
    def get_total_cost(self, obj):
        total_cost = 0
        stopover_cost = obj.stopovers.count() * 5000

        if obj.is_delivery_transferred == False:
            if obj.type == 'EVALUATION_DELIVERY':
                total_cost += obj.evaluation_cost or 0
            elif obj.type == 'INSPECTION_DELIVERY':
                total_cost += obj.inspection_cost or 0

            total_cost += (obj.delivering_cost or 0) + stopover_cost + (obj.additional_suggested_cost or 0)
        else:
            total_cost = (obj.delivering_cost or 0) + stopover_cost + (obj.additional_suggested_cost or 0)

        return total_cost


class RequestingHistorySerializer(RequestingHistoryCommonSerializer, serializers.ModelSerializer):
    car = CarSerializer(read_only=True)
    client = UserSerializer(read_only=True)
    agent = UserSerializer(read_only=True)
    deliverer = UserSerializer(read_only=True)

    source_location = CommonLocationSerializer()
    destination_location = CommonLocationSerializer()

    delivering_cost = serializers.SerializerMethodField()
    additional_costs = RequestingAdditionalCostSerializer(many=True)
    total_additional_cost = serializers.SerializerMethodField()
    total_cost = serializers.SerializerMethodField()

    delivery_result = DeliveryResultSerializer()

    is_confirmation_inspection_result = serializers.SerializerMethodField()

    class Meta:
        model = RequestingHistory
        fields = '__all__'

    @extend_schema_field(serializers.IntegerField())
    def get_delivering_cost(self, obj):
        return (obj.delivering_cost or 0) + (obj.stopovers.count() * 5000)

    @extend_schema_field(serializers.IntegerField())
    def get_total_additional_cost(self, obj):
        total_additional_cost = reduce(lambda acc, cur: acc + cur.cost, obj.additional_costs.all(), 0)

        return total_additional_cost

    @extend_schema_field(serializers.IntegerField())
    def get_total_cost(self, obj):
        user = self.context.get('user', None)

        if user == None:
            return obj.total_cost

        if obj.is_delivery_transferred == True:
            stopover_cost = obj.stopovers.count() * 5000

            return (obj.delivering_cost or 0) + (obj.additional_suggested_cost or 0) + stopover_cost
        else:
            return obj.total_cost

    @extend_schema_field(serializers.BooleanField())
    def get_is_confirmation_inspection_result(self, obj):
        return obj.confirmation_inspection_result_at != None


class DaangnRequestingRequiredDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DaangnRequestingRequiredDocument
        fields = ( 'key', 'title', 'description', 'is_optional', )


class DaangnRequestingInformationSerializer(serializers.ModelSerializer):
    is_estimated_service_date_modifiable = serializers.SerializerMethodField()
    required_documents = DaangnRequestingRequiredDocumentSerializer(many=True)

    class Meta:
        model = DaangnRequestingInformation
        fields = ( 'is_paid', 'initial_reservation_date', 'is_estimated_service_date_modifiable', 'required_documents', )

    @extend_schema_field(serializers.BooleanField())
    def get_is_estimated_service_date_modifiable(self, obj):
        now = timezone.now()

        if obj.is_paid:
            if obj.requesting_history.reservation_date is None or \
                obj.requesting_history.reservation_date <= (now + timezone.timedelta(hours=2)) :
                return True

        return False


class WorkingRequestingHistorySerializer(serializers.ModelSerializer, RequestingHistoryCommonSerializer):
    car = DetailCarSerializer(read_only=True)
    client = UserSerializer(read_only=True)
    agent = UserSerializer(read_only=True)
    deliverer = UserSerializer(read_only=True)

    source_location = CommonLocationSerializer()
    destination_location = CommonLocationSerializer()

    delivering_cost = serializers.SerializerMethodField()
    additional_costs = RequestingAdditionalCostSerializer(many=True)
    total_additional_cost = serializers.SerializerMethodField()
    total_cost = serializers.SerializerMethodField()

    delivery_result = DeliveryResultSerializer()
    review = ReviewSerializer()

    is_confirmation_inspection_result = serializers.SerializerMethodField()
    have_unread_message_from = serializers.SerializerMethodField()

    requesting_created_from = serializers.SerializerMethodField()
    daangn_requesting_information = DaangnRequestingInformationSerializer()

    class Meta:
        model = RequestingHistory
        fields = '__all__'

    def to_representation(self, instance):
        res = super(WorkingRequestingHistorySerializer, self).to_representation(instance)

        if instance.is_delivery_transferred == True:
            try:
                res['agent']['agent_location'] = None
            except:
                pass

        if instance.status == 'WAITING_WORKING' or instance.status == 'WAITING_DELIVERY_WORKING':
            now = timezone.now()

            if (instance.type != 'ONLY_DELIVERY' and instance.is_delivery_transferred == False) \
                    and instance.deliverer != None:
                return res

            if instance.estimated_service_date == None or \
                    instance.estimated_service_date > now + timezone.timedelta(minutes=30):
                if instance.type == 'ONLY_DELIVERY' or instance.is_delivery_transferred == True:
                    try:
                        res['deliverer']['agent_location'] = None
                    except:
                        pass
                else:
                    try:
                        res['agent']['agent_location'] = None
                    except:
                        pass

        return res

    @extend_schema_field(serializers.IntegerField())
    def get_delivering_cost(self, obj):
        return (obj.delivering_cost or 0) + (obj.stopovers.count() * 5000)

    @extend_schema_field(serializers.IntegerField())
    def get_total_additional_cost(self, obj):
        total_additional_cost = reduce(lambda acc, cur: acc + cur.cost, obj.additional_costs.all(), 0)

        return total_additional_cost

    @extend_schema_field(serializers.IntegerField())
    def get_total_cost(self, obj):
        user = self.context['user']

        total_cost = 0
        stopover_cost = obj.stopovers.count() * 5000
        total_additional_cost = reduce(lambda acc, cur: acc + cur.cost, obj.additional_costs.all(), 0)

        if obj.type == 'EVALUATION_DELIVERY':
            total_cost += obj.evaluation_cost or 0
        elif obj.type == 'INSPECTION_DELIVERY':
            total_cost += obj.inspection_cost or 0

        if obj.is_delivery_transferred == False:
            total_cost += (obj.delivering_cost or 0) + stopover_cost + \
                (obj.additional_suggested_cost or 0) + total_additional_cost
        else:
            if obj.deliverer == user:
                total_cost = (obj.delivering_cost or 0) + (obj.additional_suggested_cost or 0) + \
                    total_additional_cost + stopover_cost

        return total_cost

    @extend_schema_field(serializers.BooleanField())
    def get_is_confirmation_inspection_result(self, obj):
        return obj.confirmation_inspection_result_at != None

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_have_unread_message_from(self, obj):
        user = self.context['user']
        result = []

        if user == obj.client:
            unread_message_count_from_agent = obj.chatting_messages.filter(
                Q(user=obj.agent)& \
                Q(sending_to='client')& \
                ~Q(read_users=user)
            ) \
            .count()

            if unread_message_count_from_agent > 0:
                result.append('agent')

            if obj.deliverer != None:
                unread_message_count_from_deliverer = obj.chatting_messages.filter(
                    Q(user=obj.deliverer)& \
                    Q(sending_to='client')& \
                    ~Q(read_users=user)
                ) \
                .count()

                if unread_message_count_from_deliverer > 0:
                    result.append('deliverer')
        else:
            current_user_role = 'agent'

            if user == obj.agent:
                pass
            elif user == obj.deliverer:
                current_user_role = 'deliverer'

            unread_message_count_from_client = obj.chatting_messages.filter(
                Q(user=obj.client)& \
                Q(sending_to=current_user_role)& \
                ~Q(read_users=user)
            ) \
            .count()

            if unread_message_count_from_client > 0:
                result.append('client')

        return result

    @extend_schema_field(serializers.CharField())
    def get_requesting_created_from(self, obj):
        if hasattr(obj, 'daangn_requesting_information'):
            return 'DAANGN'

        return 'INTERNAL'


class LookupRequestingCostSerializer(serializers.ModelSerializer):
    source_road_address = serializers.CharField()
    destination_road_address = serializers.CharField(required=False)

    stopovers = CommonLocationSerializer(
        many=True,
        required=False,
    )

    client_id = serializers.CharField(required=False)

    class Meta:
        model = RequestingHistory
        fields = (
            'type',
            'source_road_address',
            'destination_road_address',
            'stopovers',
            'client_id',
        )


class CreateRequestingSerializer(serializers.ModelSerializer):
    reservation_date = serializers.DateTimeField(
        required=False,
    )

    car_number = serializers.CharField(help_text='차량 번호')
    car_back_image = serializers.ImageField(
        required=False,
        help_text='차량 후면 이미지',
    )

    car_type = serializers.CharField(
        required=False,
    )

    car_transmission = serializers.CharField(
        required=False,
    )

    car_classification = serializers.CharField(
        required=False,
    )

    source_road_address = serializers.CharField()
    source_detail_address = serializers.CharField()
    source_address_contact = serializers.CharField()

    destination_road_address = serializers.CharField()
    destination_detail_address = serializers.CharField()
    destination_address_contact = serializers.CharField()

    stopovers = serializers.JSONField(required=False)

    class Meta:
        model = RequestingHistory
        fields = (
            'type',
            'reservation_date',
            'memo',
            'car_number',
            'car_type',
            'car_transmission',
            'car_classification',
            'car_back_image',
            'source_road_address',
            'source_detail_address',
            'source_address_contact',
            'destination_road_address',
            'destination_detail_address',
            'destination_address_contact',
            'additional_suggested_cost',
            'stopovers',
            'is_onsite_payment',
        )

    def validate(self, data):
        requesting_type = data['type']
        destination_road_address = data.get('destination_road_address')

        if requesting_type != 'EVALUATION_DELIVERY':
            if not destination_road_address:
                raise serializers.ValidationError({ 'destination_road_address': '목적지 주소를 입력해주세요', })

        return data

    def create(self, validated_data):
        user = self.context['user']

        source_location = None
        destination_location = None

        requesting_type = validated_data['type']

        try:
            source_location = CommonLocation.objects.create(
                road_address=validated_data['source_road_address'],
                detail_address=validated_data['source_detail_address'],
                contact=validated_data.get('source_address_contact'),
            )
        except:
            raise serializers.ValidationError({ 'source_road_address': '잘못된 주소입니다.' })

        try:
            destination_location = CommonLocation.objects.create(
                road_address=validated_data['destination_road_address'],
                detail_address=validated_data['destination_detail_address'],
                contact=validated_data.get('destination_address_contact'),
            )
        except:
            raise serializers.ValidationError({ 'destination_road_address': '잘못된 주소입니다.' })

        stopovers = validated_data.get('stopovers', [])

        new_requesting = RequestingHistory.objects.create(
            client=user,
            status='WAITING_AGENT' if requesting_type != 'ONLY_DELIVERY' else 'WAITING_DELIVERER',
            type=requesting_type,
            source_location=source_location,
            destination_location=destination_location,
            is_onsite_payment=validated_data['is_onsite_payment'],
            reservation_date=validated_data.get('reservation_date', None),
            additional_suggested_cost=validated_data.get('additional_suggested_cost', 0),
            memo=validated_data.get('memo', None),
        )

        for stopover in stopovers:
            try:
                stopover_location = CommonLocation.objects.create(**stopover)
                new_requesting.stopovers.add(stopover_location)
            except:
                continue

        new_car = Car(
            requesting_history=new_requesting,
            number=validated_data['car_number'],
            type=validated_data.get('car_type', None),
            transmission=validated_data.get('car_transmission', None),
            classification=validated_data.get('car_classification', None),
            back_image=validated_data.get('car_back_image', None),
        )

        new_car.save()

        return new_requesting


class RequestingPreInformationSerializer(serializers.ModelSerializer):
    estimated_service_date = serializers.DateTimeField(help_text='예상 도착 시간')

    class Meta:
        model = RequestingHistory
        fields = ( 'estimated_service_date', )

    def validate(self, data):
        now = timezone.now()
        estimated_service_date = data['estimated_service_date']

        if now > estimated_service_date:
            raise serializers.ValidationError({ 'estimated_service_date': '도착 예정 시각은 과거일 수 없습니다.' })

        return data


class DecidePurchasingSerializer(serializers.Serializer):
    purchasing = serializers.BooleanField()

    class Meta:
        fields = ( 'purchasing', )
