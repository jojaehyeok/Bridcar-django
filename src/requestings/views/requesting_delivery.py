from django.db.models import Q
from django.contrib.gis.measure import D
from django.db.models.aggregates import Sum

from rest_framework import generics, mixins, status, serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.exceptions import ParseError, NotFound, AuthenticationFailed

from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer

from users.models import Agent
from users.permissions import IsOnlyForAgent, IsOnlyForDealer

from vehicles.models import Car
from vehicles.serializers import StartEvaluationSerializer

from requestings.models import RequestingHistory, RequestingSettlement, DeliveryResult
from requestings.serializers import RequestingHistorySerializer, RequestingDeliveryArriveSerializer, \
                                    WorkingRequestingHistorySerializer, RequestingDeliveryDepartureSerializer
from requestings.utils import handover_delivery, create_requesting_settlement
from requestings.constants import REQUESTING_TYPES

from notifications.models import Notification
from notifications.utils import KakaoAlimtalkSender, ChannelTalkGroupMessageSender

from locations.utils import distance_to_decimal_degrees

from daangn.utils import DaangnRequestingWebhookSender


@extend_schema(
    summary='탁송 양도 (평카인)',
    description='탁송 양도 (평카인) API',
    responses={
        200: WorkingRequestingHistorySerializer
    }
)
class HandoverDeliveryView(generics.GenericAPIView):
    permission_classes = [ IsOnlyForAgent ]

    def get_object(self, pk):
        user = self.request.user

        try:
            return RequestingHistory.objects.get(
                pk=pk,
                agent=user,
            )
        except RequestingHistory.DoesNotExist:
            raise NotFound

    def post(self, request, id):
        requesting_history = self.get_object(id)

        if requesting_history.status != 'WAITING_DELIVERY_WORKING':
            raise ParseError('INVALID_REQUESTING_STATUS')

        handover_delivery(requesting_history, request.user)

        return Response(
            WorkingRequestingHistorySerializer(
                requesting_history,
                context={ 'user': request.user, }
            ).data
        )


@extend_schema(
    summary='탁송 시작 (평카인)',
    description='탁송 시작 (평카인) API',
    request=RequestingDeliveryDepartureSerializer,
    responses={
        200: WorkingRequestingHistorySerializer
    }
)
class RequestingDeliveryDepartView(generics.GenericAPIView):
    parser_classes = [ MultiPartParser, ]
    permission_classes = [ IsOnlyForAgent ]
    serializer_class = RequestingDeliveryDepartureSerializer

    def get_object(self, pk):
        user = self.request.user

        try:
            return RequestingHistory.objects.get(
                Q(pk=pk)& \
                Q(deliverer=user)
            )
        except RequestingHistory.DoesNotExist:
            raise NotFound

    def post(self, request, id):
        requesting_history = self.get_object(id)

        if requesting_history.status != 'WAITING_DELIVERY_WORKING':
            raise ParseError('INVALID_REQUESTING_STATUS')

        if requesting_history.type != 'ONLY_DELIVERY':
            if requesting_history.is_delivery_transferred:
                serializer = self.get_serializer(
                    getattr(requesting_history, 'delivery_result', None),
                    data=request.data,
                    context={ 'requesting_history': requesting_history, }
                )

                if serializer.is_valid(raise_exception=True):
                    serializer.save()
            else:
                DeliveryResult.objects.create(
                    requesting_history=requesting_history,
                    mileage_before_delivery=requesting_history.car.mileage,
                )
        else:
            serializer = self.get_serializer(
                getattr(requesting_history, 'delivery_result', None),
                data=request.data,
                context={ 'requesting_history': requesting_history, }
            )

            if serializer.is_valid(raise_exception=True):
                if hasattr(requesting_history, 'daangn_requesting_information'):
                    accident_site_images = serializer.validated_data.get('accident_site_images', [])

                    if len(accident_site_images) > 0:
                        channel_talk_notification_sender = ChannelTalkGroupMessageSender(
                            f'[🥕당근의뢰]\n차량번호: { requesting_history.car.number }\n의뢰번호: { requesting_history.id }\n\n해당 탁송 의뢰에 사고사진이 등록되었습니다. 확인 후 조치 해주시기 바랍니다'
                        )

                        channel_talk_notification_sender.start()

                serializer.save()

        requesting_history.has_agent_delivery_start = True
        requesting_history.status = 'DELIVERING'
        requesting_history.save()

        Notification.create(
            [ 'USER, CONTROL_ROOM' ],
            'DEPARTURE_DELIVERY',
            user=requesting_history.client,
            actor=requesting_history.deliverer,
            requesting_history=requesting_history,
            data=requesting_history,
        )

        if requesting_history.type == 'ONLY_DELIVERY' and \
            hasattr(requesting_history, 'daangn_requesting_information'):
            webhook_sender = DaangnRequestingWebhookSender(
                requesting_history.hook_url,
                requesting_id=requesting_history.id,
                reason='REQUESTING_DELIVERY_DEPARTED',
            )

            webhook_sender.start()

        return Response(
            WorkingRequestingHistorySerializer(
                requesting_history,
                context={ 'user': request.user, },
            ).data
        )


@extend_schema(
    summary='탁송 도착 (평카인)',
    description='탁송 도착 (평카인) API',
    request=RequestingDeliveryArriveSerializer,
    responses={
        200: WorkingRequestingHistorySerializer,
    }
)
class RequestingDeliveryArriveView(generics.GenericAPIView):
    permission_classes = [ IsOnlyForAgent ]
    parser_classes = [ MultiPartParser, ]
    serializer_class = RequestingDeliveryArriveSerializer

    def get_object(self, pk):
        user = self.request.user

        try:
            return RequestingHistory.objects.get(
                Q(pk=pk)& \
                Q(deliverer=user)
            )
        except RequestingHistory.DoesNotExist:
            raise NotFound

    def post(self, request, id):
        requesting_history = self.get_object(id)

        if requesting_history.status != 'DELIVERING':
            raise ParseError('INVALID_REQUESTING_STATUS')

        serializer = self.get_serializer(requesting_history.delivery_result, data=request.data)

        if serializer.is_valid(raise_exception=True):
            serializer.save()

            if not hasattr(requesting_history, 'daangn_requesting_information'):
                requesting_history.status = 'DELIVERING_DONE'
                requesting_history.save()

                Notification.create(
                    [ 'USER, CONTROL_ROOM' ],
                    'ARRIVAL_DELIVERY',
                    user=requesting_history.client,
                    actor=requesting_history.deliverer,
                    requesting_history=requesting_history,
                    data=requesting_history,
                )

                if not requesting_history.client.is_test_account and \
                    requesting_history.client.dealer_profile.is_alimtalk_receiving:
                    KakaoAlimtalkSender(
                        template_code='DELIVERY_DONE',
                        receivers=[ str(requesting_history.client.mobile_number) ],
                        parameters={
                            'car_number': requesting_history.car.number,
                            'requesting_type': dict(REQUESTING_TYPES)[requesting_history.type],
                        }
                    ).start()

            if requesting_history.type == 'ONLY_DELIVERY' and \
                hasattr(requesting_history, 'daangn_requesting_information'):
                create_requesting_settlement(requesting_history)

                webhook_sender = DaangnRequestingWebhookSender(
                    requesting_history.hook_url,
                    requesting_id=requesting_history.id,
                    reason='REQUESTING_DELIVERY_ARRIVED',
                )

                webhook_sender.start()


            return Response(
                WorkingRequestingHistorySerializer(
                    requesting_history,
                    context={ 'user': request.user, },
                ).data
            )


@extend_schema(
    summary='탁송 인도 완료 (의뢰인)',
    description='탁송 인도 완료 (의뢰인) API',
    responses={
        200: RequestingHistorySerializer,
    }
)
class RequestingDeliveryReceivingView(generics.GenericAPIView):
    permission_classes = [ IsOnlyForDealer ]
    parser_classes = [ MultiPartParser, ]

    def get_object(self, pk):
        user = self.request.user

        try:
            return RequestingHistory.objects.get(
                pk=pk,
                client=user,
            )
        except RequestingHistory.DoesNotExist:
            raise NotFound

    def post(self, request, id):
        requesting_history = self.get_object(id)

        if requesting_history.status != 'DELIVERING_DONE':
            raise ParseError('INVALID_REQUESTING_STATUS')

        create_requesting_settlement(requesting_history)

        Notification.create(
            [ 'USER, CONTROL_ROOM' ],
            'CLIENT_CONFIRM_ARRIVAL_DELIVERY',
            user=requesting_history.deliverer,
            actor=requesting_history.client,
            requesting_history=requesting_history,
            data=requesting_history,
        )

        return Response(
            RequestingHistorySerializer(requesting_history).data
        )
