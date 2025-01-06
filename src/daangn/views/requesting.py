from typing import Generic

from django.db.models import Q
from django.utils import timezone
from django.contrib.gis.measure import D

from rest_framework import generics, mixins, status, serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.exceptions import ParseError, NotFound, AuthenticationFailed, PermissionDenied

from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer

from rest_framework_simplejwt.views import TokenRefreshView

from users.models import Agent
from users.permissions import IsOnlyDaangnAPIUser

from requestings.models import RequestingHistory
from requestings.constants import REQUESTING_STATUS

from notifications.models import Notification
from notifications.utils import KakaoAlimtalkSender

from daangn.serializers import CreateDaangnRequestingSerializer, DaangnRequestingDetailSerializer, \
                                DaangnUpdateRequestingSerializer
from daangn.utils import DaangnRequestingWebhookSender


@extend_schema(
    methods=[ 'POST', ],
    summary='탁송요청',
    description='탁송요청 API',
    request=CreateDaangnRequestingSerializer
)
class DaangnCreateRequestingView(generics.GenericAPIView):
    permission_classes = (IsOnlyDaangnAPIUser,)
    serializer_class = CreateDaangnRequestingSerializer

    def get_serializer_context(self):
        return { 'user': self.request.user, }

    def post(self, request):
        user = request.user

        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            new_requesting = serializer.save()

            close_agents = Agent.objects \
                .filter(
                    Q(agent_profile__isnull=False)& \
                    Q(agent_location__using_auto_dispatch=True)& \
                    Q(agent_location__is_end_of_work=False)& \
                    Q(
                        agent_location__coord__distance_lte=(
                            new_requesting.source_location.coord,
                            D(km=2)
                        )
                    )
                )

            if close_agents.count() > 0:
                Notification.create(
                    'USER',
                    'CREATE_REQUESTING',
                    user=close_agents,
                    actor=request.user,
                    requesting_history=new_requesting,
                    data=new_requesting,
                )

            webhook_sender = DaangnRequestingWebhookSender(
                new_requesting.hook_url,
                requesting_id=new_requesting.id,
                reason='REQUESTING_CREATED',
            )

            webhook_sender.start()

            return Response({ 'id': new_requesting.id })


@extend_schema(
    methods=[ 'GET', ],
    summary='탁송상세조회',
    description='탁송상세조회 API',
    responses={
        200: DaangnRequestingDetailSerializer,
    }
)
@extend_schema(
    methods=[ 'PATCH', ],
    summary='탁송정보변경',
    description='탁송정보변경 API',
    request=DaangnUpdateRequestingSerializer,
)
class DaangnRequestingDetailView(generics.GenericAPIView):
    permission_classes = (IsOnlyDaangnAPIUser,)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return DaangnRequestingDetailSerializer
        elif self.request.method == 'PATCH':
            return DaangnUpdateRequestingSerializer

    def get_serializer_context(self):
        return { 'user': self.request.user, }

    def get_object(self, pk):
        try:
            return RequestingHistory.objects.get(
                id=pk,
                daangn_requesting_information__isnull=False,
            )
        except RequestingHistory.DoesNotExist:
            raise NotFound('INVALID_REQUESTING')

    def get(self, request, id):
        requesting_history = self.get_object(id)

        return Response(DaangnRequestingDetailSerializer(requesting_history).data)

    def patch(self, request, id):
        requesting_history = self.get_object(id)
        serializer = self.get_serializer(requesting_history, data=request.data, partial=True)

        if serializer.is_valid(raise_exception=True):
            serializer.save()

            webhook_sender = DaangnRequestingWebhookSender(
                requesting_history.hook_url,
                requesting_id=requesting_history.id,
                reason='REQUESTING_MODIFIED',
            )

            webhook_sender.start()

            return Response(None)


@extend_schema(
    methods=[ 'POST', ],
    summary='입금완료',
    description='입금완료 API',
)
class DaangnRequestingPaymentConfirmationView(generics.GenericAPIView):
    permission_classes = (IsOnlyDaangnAPIUser,)

    def get_object(self, pk):
        try:
            return RequestingHistory.objects.get(
                id=pk,
                daangn_requesting_information__isnull=False,
            )
        except RequestingHistory.DoesNotExist:
            raise NotFound('INVALID_REQUESTING')

    def post(self, request, id):
        requesting_history = self.get_object(id)

        if requesting_history.daangn_requesting_information.is_paid is True:
            raise ParseError('ALREADY_PAID_REQUESTING')

        requesting_history.daangn_requesting_information.is_paid = True
        requesting_history.daangn_requesting_information.save()

        now = timezone.now()

        if requesting_history.reservation_date is None or \
            requesting_history.reservation_date <= (now + timezone.timedelta(hours=2)) :
            Notification.create(
                'USER',
                'DAANGN_REQUESTING_CONFIRMED',
                user=requesting_history.deliverer,
                actor=request.user,
                requesting_history=requesting_history,
                data=requesting_history
            )

            if requesting_history.deliverer is not None:
                KakaoAlimtalkSender(
                    template_code='DAANGN_REQ_CONFIRMED',
                    receivers=[ str(requesting_history.deliverer.mobile_number) ],
                    parameters={
                        'car_number': requesting_history.car.number,
                    }
                ).start()

            webhook_sender = DaangnRequestingWebhookSender(
                requesting_history.hook_url,
                requesting_id=requesting_history.id,
                reason='REQUESTING_CONFIRMED',
            )

            webhook_sender.start()

        return Response(None)


@extend_schema(
    methods=[ 'POST', ],
    summary='탁송취소',
    description='탁송취소 API',
)
class DaangnCancelRequestingView(generics.GenericAPIView):
    permission_classes = (IsOnlyDaangnAPIUser,)

    def get_object(self, pk):
        try:
            return RequestingHistory.objects.get(
                id=pk,
                daangn_requesting_information__isnull=False,
            )
        except RequestingHistory.DoesNotExist:
            raise NotFound('INVALID_REQUESTING')

    def post(self, request, id):
        requesting_history = self.get_object(id)

        if requesting_history.status == 'CANCELLED':
            raise ParseError('ALREADY_CANCELLED_REQUESTING')

        for fee_payment_history in requesting_history.fee_payment_histories.all():
            fee_payment_history.refund_fee()

        requesting_history.status = 'CANCELLED'
        requesting_history.save()

        webhook_sender = DaangnRequestingWebhookSender(
            requesting_history.hook_url,
            requesting_id=requesting_history.id,
            reason='REQUESTING_CANCELLED',
        )

        webhook_sender.start()

        response = {
            'is_require_refund': False,
        }

        requesting_status = dict(REQUESTING_STATUS)

        if requesting_history.deliverer is not None and requesting_history.has_agent_delivery_start:
            response['is_require_refund'] = True

        return Response(response)
