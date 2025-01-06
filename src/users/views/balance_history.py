from django.db.models import Q

from rest_framework import generics, mixins, status, serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import ParseError, NotFound, AuthenticationFailed

from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer

from django_filters.rest_framework import DjangoFilterBackend

from users.models import BalanceHistory, TossVirtualAccount
from users.permissions import IsOnlyForAgent
from users.serializers import BalanceHistorySerializer, RequestDepositSerializer, UserSerializer, \
                                UpdateDepositResultSerializer
from users.constants import TOSS_PAYMENTS_VIRTUAL_ACCOUNT_BANKS

@extend_schema(
    summary='입출금 내역',
    description='입출금 내역 API',
    responses={
        200: BalanceHistorySerializer,
    }
)
class BalanceHistoryListView(generics.ListAPIView):
    queryset = BalanceHistory.objects.all()
    permission_classes = (IsOnlyForAgent,)
    serializer_class = (BalanceHistorySerializer)
    filter_backends = [ DjangoFilterBackend, ]
    filterset_fields = {
        'transaction_at': [ 'range', ],
    }

    def get_queryset(self):
        agent = self.request.user

        return BalanceHistory.objects.filter(
            Q(user=agent)& \
            (
                Q(type='manual_deposit')| \
                Q(type='deposit')| \
                Q(type='withdrawal')| \
                Q(type='revenue')| \
                Q(type='fee_escrow')
            )
        ) \
        .order_by('-transaction_at')


@extend_schema(
    summary='입금 요청하기',
    description='입금 요청하기 API',
    request=RequestDepositSerializer,
    responses={
        200: UserSerializer,
        403: inline_serializer(
            name='RequestDepositErrorSerializer',
            fields={
                'detail': serializers.ChoiceField(
                    help_text=( 'NOT_ENOUGH_BALANCE: 잔고 부족<br/>' ),
                    choices={
                        'NOT_ENOUGH_BALANCE': '잔고 부족',
                    }
                ),
            }
        )
    }
)
class RequestDepositView(generics.GenericAPIView):
    permission_classes = (IsOnlyForAgent,)
    serializer_class = (RequestDepositSerializer)

    def get_serializer_context(self):
        return { 'agent': self.request.user, }

    def post(self, request):
        user = request.user

        if user.processing_virtual_account != None:
            raise ParseError('ALREADY_HAVE_VIRTUAL_ACCOUNT')

        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            TossVirtualAccount.objects.create(
                user=user,
                amount=serializer.validated_data['amount'],
                bank=serializer.validated_data['bank'],
            )

            return Response(UserSerializer(user).data)


@extend_schema(
    summary='입금 완료 Callback (TOSS)',
    description='입금 완료 Callback (TOSS) API',
    request=UpdateDepositResultSerializer,
    responses={
        200: None,
    }
)
class UpdateDepositResultView(generics.GenericAPIView):
    serializer_class = (UpdateDepositResultSerializer)

    def get_serializer_context(self):
        return { 'agent': self.request.user, }

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            if serializer.validated_data['status'] == 'DONE':
                virtual_account_history = TossVirtualAccount.objects.filter(
                    order_id=serializer.validated_data['orderId'],
                ) \
                .first()

                if virtual_account_history != None and \
                        serializer.validated_data['secret'] == virtual_account_history.secret:
                    BalanceHistory.objects.create(
                        type='deposit',
                        user=virtual_account_history.user,
                        amount=virtual_account_history.amount,
                    )

        return Response(None)
