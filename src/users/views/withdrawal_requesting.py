from rest_framework import generics, mixins, status, serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import ParseError, NotFound, AuthenticationFailed

from geopy.geocoders import Nominatim

from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer

from users.models import User
from users.permissions import IsOnlyForAgent
from users.serializers import UserSerializer, AgentCurrentLocationSerializer, \
                                RequestWithdrawalSerializer


@extend_schema(
    summary='출금 요청하기',
    description='출금 요청하기 API',
    request=RequestWithdrawalSerializer,
    responses={
        200: UserSerializer,
        403: inline_serializer(
            name='RequestWithdrawalErrorSerializer',
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
class RequestWithdrawalView(generics.GenericAPIView):
    permission_classes = (IsOnlyForAgent,)
    serializer_class = (RequestWithdrawalSerializer)

    def get_serializer_context(self):
        return { 'agent': self.request.user, }

    def post(self, request):
        user = request.user
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            serializer.save()

            return Response(UserSerializer(user).data)
