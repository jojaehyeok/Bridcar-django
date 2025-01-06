import operator
from functools import reduce
from daangn.models import daangn_requesting_information

from django.db.models import Q
from django.utils import timezone
from django.contrib.gis.measure import D
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.db.models.functions import GeometryDistance

from rest_framework import filters, generics, mixins, status, serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.exceptions import ParseError, NotFound, AuthenticationFailed, PermissionDenied

from django_filters.rest_framework import DjangoFilterBackend

from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer

from users.models import Agent, Dealer, BalanceHistory
from users.permissions import IsOnlyControlRoomUser, IsOnlyDaangnAPIUser, IsOnlyForAgent, IsOnlyForDealer

from vehicles.models import Car

from requestings.models import RequestingHistory, DeliveryFeeRelation
from requestings.serializers import RequestingHistorySerializer, RequestingPreInformationSerializer, \
                                    CreateRequestingSerializer, LookupRequestingCostSerializer, \
                                    DecidePurchasingSerializer, WorkingRequestingHistorySerializer

from requestings.constants import REQUESTING_TYPES, WORKING_REQUESTING_STATUS_KEYS
from requestings.utils import get_agent_fee, get_delivery_cost

from locations.utils import distance_to_decimal_degrees, search_road_address_from_kakao

from notifications.models import Notification
from notifications.utils import KakaoAlimtalkSender

from daangn.utils import DaangnRequestingWebhookSender


@extend_schema(
    methods=[ 'GET', ],
    summary='이용 내역 조회',
    description='이용 내역 조회 API',
    parameters=[
        OpenApiParameter(
            name='working_at',
            location=OpenApiParameter.QUERY,
            description=f'의뢰 시작 날짜 필터링',
            required=False,
            type=str
        ),
        OpenApiParameter(
            name='status',
            location=OpenApiParameter.QUERY,
            description=f'의뢰 상태 필터링 WORKING, DONE, CANCELLED',
            required=False,
            type=str
        ),
    ],
    responses={
        200: WorkingRequestingHistorySerializer
    }
)
@extend_schema(
    methods=[ 'POST', ],
    summary='의뢰 등록',
    description='의뢰 등록 API',
    request=CreateRequestingSerializer,
    responses={
        200: WorkingRequestingHistorySerializer
    }
)
class RequestingHistoryView(mixins.ListModelMixin, generics.GenericAPIView):
    queryset = RequestingHistory.objects.all()
    serializer_class = (WorkingRequestingHistorySerializer)
    parser_classes = [ MultiPartParser, ]
    filter_backends = [ DjangoFilterBackend, ]
    filterset_fields = {
        'car__number': [ 'contains', ],
    }

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateRequestingSerializer

        return WorkingRequestingHistorySerializer

    def get_serializer_context(self):
        return { 'user': self.request.user, }

    def get_queryset(self):
        status = self.request.query_params.get('status', None)
        working_at = self.request.query_params.get('working_at', None)

        queryset = RequestingHistory.objects \
            .filter(client=self.request.user) \
            .order_by('-created_at')

        if status != None and status != '':
            if status == 'WORKING':
                queryset = queryset.filter(
                    Q(status='WAITING_AGENT')| \
                    Q(status='WAITING_WORKING')| \
                    Q(status='EVALUATING')| \
                    Q(status='EVALUATION_DONE')| \
                    Q(status='WAITING_DELIVERY_WORKING')| \
                    Q(status='DELIVERING')| \
                    Q(status='DELIVERING_DONE')
                )
            else:
                queryset = queryset.filter(status=status)

        if working_at != None:
            splitted_working_at = working_at.split(',')

            if len(splitted_working_at) == 2:
                queryset = RequestingHistory.objects \
                    .filter(
                        Q(reservation_date__date__range=[ splitted_working_at[0], splitted_working_at[1] ])| \
                        (
                            Q(reservation_date__isnull=True)& \
                            Q(created_at__date__range=[ splitted_working_at[0], splitted_working_at[1], ])
                        )
                    )

        return queryset

    def get(self, request, *args, **kwargs):
        return super(RequestingHistoryView, self).list(request, *args, **kwargs)

    def post(self, request):
        user = request.user
        serializer = self.get_serializer(
            data=request.data,
            context={ 'user': user, },
        )

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
                    actor=user,
                    requesting_history=new_requesting,
                    data=new_requesting
                )

            Notification.create(
                'CONTROL_ROOM',
                'CREATE_REQUESTING',
                user=None,
                actor=user,
                requesting_history=new_requesting,
                send_fcm=False,
            )

            return Response(
                WorkingRequestingHistorySerializer(
                    new_requesting,
                    context={ 'user': user, }
                ).data
            )


@extend_schema(
    methods=[ 'POST', ],
    summary='평카 신청 요금 조회',
    description='평카 신청 요금 조회 API',
    request=LookupRequestingCostSerializer,
    responses={
        200: inline_serializer(
            name='LookupRequestingCostResultSerializer',
            fields={
                'evaluation_cost': serializers.IntegerField(),
                'inspection_cost': serializers.IntegerField(),
                'delivery_cost': serializers.IntegerField(),
            },
        ),
    }
)
class LookupRequestingCostView(generics.GenericAPIView):
    permission_classes = [ (IsOnlyForDealer | IsOnlyDaangnAPIUser | IsOnlyControlRoomUser) ]
    serializer_class = (LookupRequestingCostSerializer)

    def post(self, request):
        user = request.user
        serializer = self.get_serializer(data=request.data)


        if serializer.is_valid(raise_exception=True):
            evaluation_cost = 0
            inspection_cost = 0
            delivery_cost = 0

            if user.is_superuser == True:
                client_id = serializer.validated_data.get('client_id')

                if not user.is_dealer and not client_id:
                    raise ParseError('INVALID_CLIENT_ID')

                if client_id:
                    try:
                        user = Dealer.objects.get(id=client_id)
                    except Dealer.DoesNotExist:
                        raise NotFound('INVALID_DEALER_ID')

            requesting_type = serializer.validated_data['type']

            source_road_address = serializer.validated_data.get('source_road_address')
            destination_road_address = serializer.validated_data.get('destination_road_address')
            stopovers = serializer.validated_data.get('stopovers', [])
            delivery_cost = get_delivery_cost(source_road_address, destination_road_address)

            if requesting_type == 'EVALUATION_DELIVERY':
                evaluation_cost = user.dealer_profile.basic_evaluation_cost
            elif requesting_type == 'INSPECTION_DELIVERY':
                inspection_cost = user.dealer_profile.basic_inspection_cost

            delivery_cost += len(stopovers) * 5000

            return Response({
                'evaluation_cost': evaluation_cost,
                'inspection_cost': inspection_cost,
                'delivery_cost': delivery_cost,
            })

@extend_schema(
    summary='배차 대기중 내역 조회',
    description='배차 대기중 내역 API',
    parameters=[
        OpenApiParameter(
            name='type',
            location=OpenApiParameter.QUERY,
            description=f'의뢰 구분 ({ " / ".join(dict(REQUESTING_TYPES).keys()) })',
            required=False,
            type=str
        ),
        OpenApiParameter(
            name='distance',
            location=OpenApiParameter.QUERY,
            description='거리 필터 (km)',
            required=False,
            type=float
        ),
    ],
    responses={
        200: RequestingHistorySerializer
    }
)
class WaitingAllocationsRequestingHistoryView(generics.ListAPIView):
    permission_classes = [ IsOnlyForAgent ]
    serializer_class = (RequestingHistorySerializer)

    def get_serializer_context(self):
        return { 'user': self.request.user, }

    def get_queryset(self):
        user = self.request.user

        requesting_type = self.request.query_params.get('type', None)
        distance = self.request.query_params.get('distance', None)

        queryset = RequestingHistory.objects \
            .filter(
                Q(client__isnull=False)& \
                (
                    Q(status='WAITING_AGENT')& \
                    Q(agent__isnull=True)
                )| \
                (
                    Q(status='WAITING_DELIVERER')& \
                    ~Q(agent=user)& \
                    Q(deliverer__isnull=True)
                )
            ) \
            .exclude(
                Q(daangn_requesting_information__is_paid=False)& \
                Q(daangn_requesting_information__is_forced_exposure=False)
            )

        '''
        queryset = queryset.exclude(
            Q(daangn_requesting_information__isnull=False)& \
            Q(daangn_requesting_information__is_paid=False)
        )
        '''

        if requesting_type != None:
            if user.agent_profile.level == 'B':
                if requesting_type == 'EVALUATION_DELIVERY':
                    requesting_type = None
            elif user.agent_profile.level == 'C':
                if requesting_type != 'ONLY_DELIVERY':
                    requesting_type = None

            if requesting_type != None:
                queryset = queryset.filter(type=requesting_type)
        else:
            requesting_types = list(dict(REQUESTING_TYPES).keys())

            if user.agent_profile.level == 'A':
                queryset = queryset.filter(type__in=requesting_types)
            elif user.agent_profile.level == 'B':
                queryset = queryset.filter(type__in=requesting_types.remove('EVALUATION_DELIVERY'))
            else:
                queryset = queryset.filter(type='ONLY_DELIVERY')

        if distance != None:
            if float(distance) < 100:
                if user.agent_location.coord != None and not user.agent_location.using_manual_address:
                    queryset = queryset.filter(
                        source_location__coord__dwithin=(
                            user.agent_location.coord,
                            distance_to_decimal_degrees(D(km=distance), user.agent_location.coord.coords[1])
                        )
                    ) \
                    .annotate(distance=GeometryDistance('source_location__coord', user.agent_location.coord)) \
                    .order_by('distance')
                elif user.agent_location.manual_coord != None and user.agent_location.using_manual_address:
                    queryset = queryset.filter(
                        source_location__coord__dwithin=(
                            user.agent_location.manual_coord,
                            distance_to_decimal_degrees(D(km=distance), user.agent_location.manual_coord.coords[1])
                        )
                    ) \
                    .annotate(distance=GeometryDistance('source_location__coord', user.agent_location.manual_coord)) \
                    .order_by('distance')
            else:
                if user.agent_location.coord != None and not user.agent_location.using_manual_address:
                    queryset = queryset \
                        .annotate(distance=GeometryDistance('source_location__coord', user.agent_location.coord)) \
                        .order_by('distance')
                elif user.agent_location.manual_coord != None and user.agent_location.using_manual_address:
                    queryset = queryset \
                        .annotate(distance=GeometryDistance('source_location__coord', user.agent_location.manual_coord)) \
                        .order_by('distance')

        return queryset

    def get(self, request, *args, **kwargs):
        user = request.user

        if user.agent_location.coord is None:
            raise ParseError('INVALID_AGENT_LOCATION')

        return super(WaitingAllocationsRequestingHistoryView, self).list(request, *args, **kwargs)


@extend_schema(
    methods=[ 'GET', ],
    summary='배차 대기중인 내역 디테일 조회',
    description='배차 대기중인 내역 디테일 조회 API',
    responses={
        200: WorkingRequestingHistorySerializer
    }
)
class WaitingAllocationsRequestingHistoryDetailView(generics.GenericAPIView):
    permission_classes = [ IsOnlyForAgent ]

    def get_object(self, pk):
        return RequestingHistory.objects.get(pk=pk)

    def get(self, request, id):
        requesting_history = self.get_object(id)

        return Response(WorkingRequestingHistorySerializer(
            requesting_history,
            context={ 'user': request.user, },
        ).data)


@extend_schema(
    summary='현재 작업중인 내역 조회',
    description='현재 작업중인 내역 조회 API',
    parameters=[
        OpenApiParameter(
            name='working_at',
            location=OpenApiParameter.QUERY,
            description=f'의뢰 시작 날짜 필터링',
            required=False,
            type=str
        ),
    ],
    responses={
        200: WorkingRequestingHistorySerializer
    }
)
class WorkingRequestingHistoryView(generics.ListAPIView):
    queryset = RequestingHistory.objects.all()
    permission_classes = [ IsOnlyForAgent ]
    serializer_class = (WorkingRequestingHistorySerializer)
    filter_backends = [ DjangoFilterBackend, ]
    filterset_fields = {
        'car__number': [ 'contains', ],
    }

    def get_serializer_context(self):
        return { 'user': self.request.user, }

    def get_queryset(self):
        working_at = self.request.query_params.get('working_at', None)

        queryset = RequestingHistory.objects \
            .filter(
                (
                    Q(agent=self.request.user)| \
                    Q(deliverer=self.request.user)
                )& \
                (
                    ~Q(status='DONE')& \
                    ~Q(status='CANCELLED')
                )
            ) \
            .exclude(
                Q(agent=self.request.user)& \
                Q(is_delivery_transferred=True)
            ) \
            .order_by('-created_at')

        if working_at != None:
            splitted_working_at = working_at.split(',')

            if len(splitted_working_at) == 2:
                queryset = queryset \
                    .filter(
                        Q(reservation_date__date__range=[ splitted_working_at[0], splitted_working_at[1] ])| \
                        (
                            Q(reservation_date__isnull=True)& \
                            Q(created_at__date__range=[ splitted_working_at[0], splitted_working_at[1] ],)
                        )
                    )

        return queryset

    def get(self, request, *args, **kwargs):
        user = request.user

        if user.agent_location.coord is None:
            raise ParseError('INVALID_AGENT_LOCATION')

        return super(WorkingRequestingHistoryView, self).list(request, *args, **kwargs)


@extend_schema(
    summary='완료한 작업내역 조회',
    description='완료한 작업내역 조회 API',
    parameters=[
        OpenApiParameter(
            name='working_at',
            location=OpenApiParameter.QUERY,
            description=f'의뢰 시작 날짜 필터링',
            required=False,
            type=str
        ),
    ],
    responses={
        200: WorkingRequestingHistorySerializer
    }
)
class FinishesRequestingHistoryView(generics.ListAPIView):
    queryset = RequestingHistory.objects.all()
    permission_classes = [ IsOnlyForAgent ]
    serializer_class = (WorkingRequestingHistorySerializer)
    filter_backends = [ DjangoFilterBackend, ]
    filterset_fields = {
        'car__number': [ 'exact', ],
        #'settlement__requesting_end_at': [ 'range', ],
    }

    def get_serializer_context(self):
        return { 'user': self.request.user, }

    def get_queryset(self):
        working_at = self.request.query_params.get('working_at', None)

        queryset = self.queryset.filter(
            (
                Q(status='DONE')& \
                (
                    Q(agent=self.request.user)| \
                    Q(deliverer=self.request.user)
                )
            )|\
            (
                Q(agent=self.request.user)& \
                Q(is_delivery_transferred=True)
            )
        )

        if working_at != None:
            splitted_working_at = working_at.split(',')

            if len(splitted_working_at) == 2:
                queryset = queryset \
                    .filter(
                        Q(reservation_date__date__range=[ splitted_working_at[0], splitted_working_at[1] ])| \
                        (
                            Q(reservation_date__isnull=True)& \
                            Q(created_at__date__range=[ splitted_working_at[0], splitted_working_at[1], ])
                        )
                    )

        return queryset


@extend_schema(
    methods=[ 'GET', ],
    summary='이용 내역 디테일 조회',
    description='이용 내역 디테일 조회 API',
    responses={
        200: WorkingRequestingHistorySerializer
    }
)
@extend_schema(
    methods=[ 'DELETE', ],
    summary='의뢰 신청 취소',
    description='의뢰 신청 취소 API',
)
class RequestingHistoryDetailView(generics.GenericAPIView):
    def get_object(self, pk):
        is_agent = True

        if not hasattr(self.request.user, 'agent_profile'):
            is_agent = False

        try:
            if is_agent:
                return RequestingHistory.objects.get(
                    Q(pk=pk)& \
                    (
                        Q(agent=self.request.user)| \
                        Q(deliverer=self.request.user)
                    )
                )
            else:
                return RequestingHistory.objects.get(
                    pk=pk,
                    client=self.request.user,
                )
        except RequestingHistory.DoesNotExist:
            raise NotFound

    def get(self, request, id):
        requesting_history = self.get_object(id)

        return Response(WorkingRequestingHistorySerializer(
            requesting_history,
            context={ 'user': request.user, },
        ).data)

    def delete(self, request, id):
        requesting_history = self.get_object(id)

        if requesting_history.status == 'WAITING_AGENT' or \
                requesting_history.status == 'WAITING_DELIVERER':
            requesting_history.status = 'CANCELLED'
            requesting_history.save()
        else:
            raise PermissionDenied('INVALID_REQUESTING_STATUS')

        return Response(None)


@extend_schema(
    summary='요금 확인 (Confirm)',
    description='요금 확인 (Confirm) API',
    responses={
        200: RequestingHistorySerializer
    }
)
class RequestingCostView(generics.GenericAPIView):
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

        if requesting_history.status != 'REQUESTED':
            raise PermissionDenied('INVALID_REQUESTING_STATUS')

        if requesting_history.evaluation_cost == None and requesting_history.delivering_cost == None:
            raise ParseError('INVALID_COST')

        requesting_history.status = 'WAITING_AGENT'
        requesting_history.save()

        return Response(RequestingHistorySerializer(requesting_history).data)


@extend_schema(
    summary='배차 지원하기',
    description='배차 지원하기 API',
    responses={
        200: WorkingRequestingHistorySerializer,
        403: inline_serializer(
            name='ApplyRequestingErrorSerializer',
            fields={
                'detail': serializers.ChoiceField(
                    help_text=(
                        'NOT_ENOUGH_BALANCE: 수수료 부족<br/>',
                        'INVALID_REQUESTING_STATUS: 올바르지 않은 의뢰 상태<br/>',
                    ),
                    choices={
                        'NOT_ENOUGH_BALANCE': '수수료 부족',
                        'INVALID_REQUESTING_STATUS': '올바르지 않은 의뢰 상태',
                    }
                ),
            }
        )
    }
)
class ApplyRequestingView(generics.GenericAPIView):
    def get_object(self, pk):
        try:
            return RequestingHistory.objects.get(pk=pk)
        except RequestingHistory.DoesNotExist:
            raise NotFound

    def post(self, request, id):
        agent = request.user
        requesting_history = self.get_object(id)

        if requesting_history.type == 'ONLY_DELIVERY':
            if requesting_history.status != 'WAITING_DELIVERER':
                raise PermissionDenied('INVALID_REQUESTING_STATUS')
        else:
            if requesting_history.status != 'WAITING_AGENT' and requesting_history.status != 'WAITING_DELIVERER':
                raise PermissionDenied('INVALID_REQUESTING_STATUS')

        if agent.agent_profile.insurance_expiry_date is None or \
            agent.agent_profile.insurance_expiry_date < timezone.now().date():
            raise PermissionDenied('INSURANCE_EXPIRED')

        fee = get_agent_fee(requesting_history)

        if agent.agent_profile.balance < fee:
            raise PermissionDenied('NOT_ENOUGH_BALANCE')

        balance_history_sub_type = 'agent'

        if requesting_history.type == 'ONLY_DELIVERY':
            balance_history_sub_type = 'deliverer'
        elif requesting_history.is_delivery_transferred:
            balance_history_sub_type = 'deliverer'

        balance_history = BalanceHistory.objects.create(
            user=agent,
            amount=fee,
            type='fee_escrow',
            sub_type=balance_history_sub_type,
        )

        if requesting_history.type == 'ONLY_DELIVERY':
            requesting_history.status = 'WAITING_DELIVERY_WORKING'
            requesting_history.deliverer = request.user
        else:
            if requesting_history.status == 'WAITING_DELIVERER':
                requesting_history.status = 'WAITING_DELIVERY_WORKING'
                requesting_history.deliverer = request.user
            else:
                requesting_history.agent = request.user
                requesting_history.status = 'WAITING_WORKING'

        requesting_history.fee_payment_histories.add(balance_history)
        requesting_history.save()

        if not requesting_history.client.is_test_account:
            requesting_type = requesting_history.type

            if requesting_type == 'EVALUATION_DELIVERY' and \
                    requesting_history.is_delivery_transferred == True:
                requesting_type = 'ONLY_DELIVERY'

            if requesting_history.client.dealer_profile.is_alimtalk_receiving:
                KakaoAlimtalkSender(
                    template_code='ASSIGN_AGENT',
                    receivers=[ str(requesting_history.client.mobile_number) ],
                    parameters={
                        'car_number': requesting_history.car.number,
                        'requesting_type': dict(REQUESTING_TYPES)[requesting_type],
                        'agent_name': request.user.name,
                    }
                ).start()

        if requesting_history.type == 'ONLY_DELIVERY' and \
            hasattr(requesting_history, 'daangn_requesting_information'):
            webhook_sender = DaangnRequestingWebhookSender(
                requesting_history.hook_url,
                requesting_id=requesting_history.id,
                reason='REQUESTING_AGENT_APPLIED',
            )

            webhook_sender.start()

            now = timezone.now()

            if requesting_history.daangn_requesting_information.is_paid is True:
                if requesting_history.reservation_date is None or \
                    requesting_history.reservation_date <= (now + timezone.timedelta(hours=2)) :
                    KakaoAlimtalkSender(
                        template_code='DAANGN_REQ_CONFIRMED',
                        receivers=[ str(requesting_history.deliverer.mobile_number) ],
                        parameters={
                            'car_number': requesting_history.car.number,
                        }
                    ).start()

        return Response(
            WorkingRequestingHistorySerializer(
                requesting_history,
                context={ 'user': agent, },
            ).data)


@extend_schema(
    summary='업무 시작전 정보 입력',
    description='업무 시작전 정보 입력 API',
    request=RequestingPreInformationSerializer,
    responses={
        200: WorkingRequestingHistorySerializer
    }
)
class RequestingPreInformationView(generics.GenericAPIView):
    serializer_class = RequestingPreInformationSerializer

    def get_object(self, pk):
        try:
            return RequestingHistory.objects.get(
                Q(pk=pk)& \
                (
                    Q(agent=self.request.user)| \
                    Q(deliverer=self.request.user)
                )
            )
        except RequestingHistory.DoesNotExist:
            raise NotFound

    def post(self, request, id):
        requesting_history = self.get_object(id)

        if requesting_history.type == 'ONLY_DELIVERY':
            if requesting_history.status != 'WAITING_DELIVERY_WORKING':
                raise PermissionDenied('INVALID_REQUESTING_STATUS')
        else:
            if requesting_history.status != 'WAITING_WORKING' and requesting_history.status != 'WAITING_DELIVERY_WORKING':
                raise PermissionDenied('INVALID_REQUESTING_STATUS')

        serializer = self.get_serializer(requesting_history, data=request.data)

        if serializer.is_valid(raise_exception=True):
            serializer.save()

            if requesting_history.type == 'ONLY_DELIVERY' and \
                hasattr(requesting_history, 'daangn_requesting_information'):
                webhook_sender = DaangnRequestingWebhookSender(
                    requesting_history.hook_url,
                    requesting_id=requesting_history.id,
                    reason='REQUESTING_ESTIMATED_SERVICE_DATE_UPDATED',
                )

                webhook_sender.start()

            return Response(
                WorkingRequestingHistorySerializer(
                    requesting_history,
                    context={ 'user': request.user, }
                ).data
            )


@extend_schema(
    summary='매입 여부 결정 (의뢰인)',
    description='매입 여부 결정 API',
    request=DecidePurchasingSerializer,
    responses={
        200: WorkingRequestingHistorySerializer
    }
)
class DecidePurchasingView(generics.GenericAPIView):
    serializer_class = RequestingPreInformationSerializer
    permission_classes = [ IsOnlyForDealer, ]

    def get_object(self, pk):
        try:
            return RequestingHistory.objects.get(
                pk=pk,
                client=self.request.user,
            )
        except RequestingHistory.DoesNotExist:
            raise NotFound

    def put(self, request, id):
        requesting_history = self.get_object(id)

        if requesting_history.status != 'EVALUATION_DONE':
            raise PermissionDenied('INVALID_REQUESTING_STATUS')

        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            will_purchasing = serializer.validated_data['purchasing']

            if will_purchasing:
                requesting_history.deliverer = requesting_history.agent
                requesting_history.status = 'WAITING_DELIVERY_WORKING'
                requesting_history.delivery_proceed_decided_at = timezone.now()
            else:
                requesting_history.status = 'WAITING_DELIVERER'

            requesting_history.save()

            Notification.create(
                [ 'USER', 'CONTROL_ROOM', ],
                'CLIENT_PURCHASE_DECISION',
                user=requesting_history.client,
                actor=requesting_history.agent,
                requesting_history=requesting_history,
                data=requesting_history,
            )

            return Response(
                WorkingRequestingHistorySerializer(
                    requesting_history,
                    context={ 'user': request.user, },
                ).data
            )
