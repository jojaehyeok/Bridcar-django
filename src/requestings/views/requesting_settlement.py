from pytz import timezone
from urllib.parse import quote

from django.db.models import Q
from django.http.response import HttpResponse

from rest_framework import generics, mixins, status, serializers
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.exceptions import ParseError, NotFound, AuthenticationFailed, PermissionDenied

from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer

from users.permissions import IsOnlyForAgent, IsOnlyForDealer

from requestings.models import RequestingSettlement
from requestings.serializers import RequestingSettlementSerializer
from requestings.utils import generate_requesting_settlement_xlsx


@extend_schema(
    summary='의뢰 정산 내역 조회',
    description='의뢰 정산 내역 조회 API',
    parameters=[
        OpenApiParameter(
            name='year',
            location=OpenApiParameter.QUERY,
            description='정산 내역을 불러올 년도',
            required=True,
            type=str
        ),
        OpenApiParameter(
            name='month',
            location=OpenApiParameter.QUERY,
            description='정산 내역을 불러올 월',
            required=True,
            type=str
        ),
    ],
    responses={
        200: inline_serializer(
            name='RequestingSettlementResponseSerializer',
            fields={
                'total_requesting_count': serializers.IntegerField(),
                'total_requesting_charge': serializers.IntegerField(),
                'total_requesting_fees': serializers.IntegerField(),
                'settlements': serializers.ListField(
                    child=inline_serializer(
                        name='RequestingNestedDailySerializer',
                        fields={
                            'day': serializers.IntegerField(),
                            'total_requesting_count': serializers.IntegerField(),
                            'total_charge': serializers.IntegerField(),
                            'total_fees': serializers.IntegerField(),
                        }
                    )
                ),
            }
        )
    }
)
class RequestingSettlementView(generics.GenericAPIView):
    pagination_class = None
    serializer_class = (RequestingSettlementSerializer)
    permission_classes = ( IsOnlyForAgent, )

    def get_queryset(self, year, month):
        return RequestingSettlement.objects.filter(
            user=self.request.user,
            requesting_end_at__year=year,
            requesting_end_at__month=month,
        )

    def get(self, request):
        user = request.user
        year = request.query_params.get('year')
        month = request.query_params.get('month')

        requesting_settlements = self.get_queryset(year, month)

        result = {
            'settlements': [],
            'total_requesting_count': 0,
        }

        daily_settlement_table = {}

        total_charge = 0
        total_fees = 0

        for settlement in requesting_settlements:
            fee = 0
            total_cost = settlement.evaluation_cost + settlement.inspection_cost + settlement.delivering_cost + \
                settlement.total_additional_cost + settlement.additional_suggested_cost

            day = settlement.requesting_end_at.astimezone(timezone('Asia/Seoul')).day

            daily_settlement_index = daily_settlement_table.get(day, None)

            fee_payment_history = settlement.requesting_history.fee_payment_histories \
                .filter(user=user) \
                .first()

            if fee_payment_history != None:
                fee = fee_payment_history.amount

            if daily_settlement_index == None:
                new_daily_settlement = {
                    'day': day,
                    'total_requesting_count': 1,
                    'total_charge': total_cost,
                    'total_fees': fee,
                }

                result['settlements'].append(new_daily_settlement)
                daily_settlement_table[day] = len(result['settlements']) - 1
            else:
                result['settlements'][daily_settlement_index]['total_requesting_count'] += 1
                result['settlements'][daily_settlement_index]['total_charge'] += total_cost
                result['settlements'][daily_settlement_index]['total_fees'] += fee

            total_charge += total_cost
            total_fees += fee

        result['total_requesting_count'] = len(requesting_settlements)
        result['total_requesting_charge'] = total_charge
        result['total_requesting_fees'] = total_fees

        return Response(result)


@extend_schema(
    methods=[ 'GET', ],
    summary='정산 내역 엑셀 다운로드',
    description='정산 내역 엑셀 다운로드',
    parameters=[
        OpenApiParameter(
            name='year',
            location=OpenApiParameter.QUERY,
            description='정산 내역을 다운받을 년도',
            required=True,
            type=int
        ),
        OpenApiParameter(
            name='month',
            location=OpenApiParameter.QUERY,
            description='정산 내역을 다운받을 년도',
            required=True,
            type=int
        ),
        OpenApiParameter(
            name='exists_check_only',
            location=OpenApiParameter.QUERY,
            description='해당 년월에 정산기록 존재 유무만 확인',
            required=False,
            type=bool
        ),
    ],
)
class MonthlyRequestingSettlementView(APIView):
    def get(self, request, date=None):
        user = request.user

        target_year = request.query_params.get('year')
        target_month = request.query_params.get('month')
        exists_check_only = request.query_params.get('exists_check_only')

        settlements = []

        if user.is_dealer:
            if user.dealer_profile.company is not None:
                settlements = RequestingSettlement.objects \
                    .filter(
                        Q(requesting_history__client__dealer_profile__company=user.dealer_profile.company)& \
                        Q(requesting_end_at__year=target_year)& \
                        Q(requesting_end_at__month=target_month)
                    )
            else:
                settlements = RequestingSettlement.objects \
                    .filter(
                        Q(requesting_history__client=user)& \
                        Q(requesting_end_at__year=target_year)& \
                        Q(requesting_end_at__month=target_month)
                    )
        else:
            settlements = RequestingSettlement.objects \
                .filter(
                    Q(user=user)& \
                    Q(requesting_end_at__year=target_year)& \
                    Q(requesting_end_at__month=target_month)
                )

        if settlements.count() == 0:
            raise NotFound('SETTLEMENTS_NOT_EXISTS')

        if exists_check_only:
            return Response(None)

        xlsx_output = generate_requesting_settlement_xlsx(
            settlements,
            custom_title=f'{ user.name } 평가사 { target_year }년 { target_month }월 정산목록' if user.is_agent else '',
            for_agent=True if user.is_agent else False,
        )

        response = HttpResponse(
            xlsx_output,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

        filename = '정산내역.xlsx'
        response['Content-Disposition'] = "attachment; filename*=UTF-8''{}".format(quote(filename.encode('utf-8')))

        return response
