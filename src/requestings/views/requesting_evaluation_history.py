import json

from asgiref.sync import async_to_sync
from django.db.models.aggregates import Sum

from django.utils import timezone

from rest_framework import generics, mixins, status, serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.exceptions import PermissionDenied, ParseError, NotFound, AuthenticationFailed

from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer

from users.permissions import IsOnlyForAgent, IsOnlyForDealer

from vehicles.models import Car
from vehicles.serializers import StartEvaluationSerializer

from requestings.models import RequestingHistory, RequestingSettlement
from requestings.serializers import RequestingHistorySerializer, WorkingRequestingHistorySerializer, \
                                    ConfirmRequestingEvaluationSerializer
from requestings.constants import REQUESTING_TYPES

from notifications.models import Notification
from notifications.utils import KakaoAlimtalkSender

from pcar.utils import RedisQueue


@extend_schema(
    summary='평카 시작 (평카인)',
    description='평카 시작 (평카인) API',
    request=StartEvaluationSerializer,
    responses={
        200: WorkingRequestingHistorySerializer
    }
)
class StartRequestingEvaluationView(generics.GenericAPIView):
    serializer_class = (StartEvaluationSerializer)
    permission_classes = [ IsOnlyForAgent ]
    parser_classes = (MultiPartParser,)

    def get_object(self, pk):
        try:
            return RequestingHistory.objects.get(pk=pk)
        except RequestingHistory.DoesNotExist:
            raise NotFound

    def post(self, request, id):
        requesting_history = self.get_object(id)

        if requesting_history.status != 'WAITING_WORKING':
            raise PermissionDenied('INVALID_REQUESTING_STATUS')

        serializer = self.get_serializer(requesting_history.car, data=request.data)

        if serializer.is_valid(raise_exception=True):
            serializer.save()

            requesting_history.status = 'EVALUATING'
            requesting_history.save()

            Notification.create(
                [ 'USER, CONTROL_ROOM' ],
                'START_EVALUATION',
                user=requesting_history.client,
                actor=requesting_history.agent,
                requesting_history=requesting_history,
                data=requesting_history,
            )

            return Response(
                WorkingRequestingHistorySerializer(
                    requesting_history,
                    context={ 'user': request.user, }
                ).data
            )


@extend_schema(
    summary='평카 완료하기 (평카인)',
    description='평카 완료하기 (평카인) API',
    responses={
        200: WorkingRequestingHistorySerializer
    }
)
class FinishRequestingEvaluationView(generics.GenericAPIView):
    permission_classes = [ IsOnlyForAgent ]

    def get_object(self, pk):
        try:
            return RequestingHistory.objects.get(pk=pk)
        except RequestingHistory.DoesNotExist:
            raise NotFound

    def post(self, request, id):
        requesting_history = self.get_object(id)

        if (requesting_history.type != 'EVALUATION_DELIVERY' and requesting_history.type != 'INSPECTION_DELIVERY') \
                and requesting_history.status != 'EVALUATING':
            raise PermissionDenied('INVALID_REQUESTING_STATUS')

        if not hasattr(requesting_history.car, 'evaluation_result') or \
                requesting_history.car.evaluation_result.images.count() == 0:
            raise ParseError('EVALUATION_NOT_COMPLETED')

        requesting_history.evaluation_finished_at = timezone.now()

        if requesting_history.type == 'EVALUATION_DELIVERY':
            requesting_history.status = 'EVALUATION_DONE'
        elif requesting_history.type == 'INSPECTION_DELIVERY':
            requesting_history.status = 'WAITING_DELIVERY_WORKING'
            requesting_history.deliverer = requesting_history.agent

        requesting_history.save()

        Notification.create(
            [ 'USER, CONTROL_ROOM' ],
            'FINISH_EVALUATION',
            user=requesting_history.client,
            actor=requesting_history.agent,
            requesting_history=requesting_history,
            data=requesting_history,
        )

        if requesting_history.type == 'EVALUATION_DELIVERY':
            if not requesting_history.client.is_test_account:
                KakaoAlimtalkSender(
                    template_code='EVALUATION_DONE',
                    receivers=[ str(requesting_history.client.mobile_number) ],
                    parameters={
                        'car_number': requesting_history.car.number,
                        'requesting_type': dict(REQUESTING_TYPES)[requesting_history.type],
                    }
                ).start()
        elif requesting_history == 'INSPECTION_DELIVERY':
            if not requesting_history.client.is_test_account:
                KakaoAlimtalkSender(
                    template_code='INSPECTION_DELIVERY',
                    receivers=[ str(requesting_history.client.mobile_number) ],
                    parameters={
                        'car_number': requesting_history.car.number,
                        'requesting_type': dict(REQUESTING_TYPES)[requesting_history.type],
                    }
                ).start()

        return Response(
            WorkingRequestingHistorySerializer(
                requesting_history,
                context={ 'user': request.user, },
            ).data
        )


@extend_schema(
    summary='검수 결과 확인하기 (의뢰인)',
    description='검수 결과 확인하기 (의뢰인) API',
    responses={
        200: RequestingHistorySerializer
    }
)
class ConfirmInspectionResultView(generics.GenericAPIView):
    permission_classes = [ IsOnlyForDealer, ]

    def get_object(self, pk):
        try:
            return RequestingHistory.objects.get(pk=pk)
        except RequestingHistory.DoesNotExist:
            raise NotFound

    def post(self, request, id):
        requesting_history = self.get_object(id)

        if requesting_history.evaluation_finished_at == None:
            raise PermissionDenied('INVALID_REQUESTING_STATUS')

        requesting_history.confirmation_inspection_result_at = timezone.now()
        requesting_history.save()

        return Response(
            RequestingHistorySerializer(requesting_history).data
        )


@extend_schema(
    summary='평카 종료 (딜러, 매입유무 결정)',
    description='평카 종료 (딜러, 매입유무 결정) API',
    responses={
        200: RequestingHistorySerializer
    }
)
class ConfirmRequestingEvaluationView(generics.GenericAPIView):
    serializer_class = ConfirmRequestingEvaluationSerializer

    def get_object(self, pk):
        try:
            return RequestingHistory.objects.get(
                pk=pk,
                client=self.request.user,
            )
        except RequestingHistory.DoesNotExist:
            raise NotFound

    def post(self, request, id):
        requesting_history = self.get_object(id)

        if requesting_history.type != 'EVALUATION_DELIVERY' or requesting_history.status != 'EVALUATION_DONE':
            raise PermissionDenied('INVALID_REQUESTING_STATUS')

        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            need_delivery = serializer.validated_data['need_delivery']

            if need_delivery:
                requesting_history.deliverer = requesting_history.agent
                requesting_history.status = 'WAITING_DELIVERY_WORKING'
            else:
                requesting_history.status = 'DONE'

                total_additional_costs = requesting_history.additional_costs \
                    .filter(working_type='EVALUATION/INSPECTION')

                settlement = RequestingSettlement.objects.create(
                    requesting_history=requesting_history,
                    user=requesting_history.agent,
                    evaluation_cost=requesting_history.evaluation_cost,
                    inspection_cost=requesting_history.inspection_cost,
                    is_onsite_payment=requesting_history.is_onsite_payment,
                )

                settlement.additional_costs.add(*total_additional_costs)

            requesting_history.save()

            if requesting_history.type == 'EVALUATION_DELIVERY':
                requesting_history.agent.agent_profile.total_evaluation_count += 1
            elif requesting_history.type == 'INSPECTION_DELIVERY':
                requesting_history.agent.agent_profile.total_inspection_count += 1

            requesting_history.agent.agent_profile.save()

        return Response(RequestingHistorySerializer(requesting_history).data)

