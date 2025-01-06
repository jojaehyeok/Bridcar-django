from django.contrib.gis.geos.geometry import GEOSGeometry

from rest_framework import generics, mixins, status, serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.exceptions import ParseError, NotFound, AuthenticationFailed

from geopy.geocoders import Nominatim

from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer

from users.models import AgentSettlementAccount
from users.serializers import UserSerializer, AgentSettlementAccountSerializer, UpdateAgentProfileSerializer
from users.permissions import IsOnlyForAgent


@extend_schema(
    methods=[ 'PATCH', ],
    summary='평카인 프로필 수정',
    description='평카인 프로필 수정 API',
    request=UpdateAgentProfileSerializer,
    responses={
        200: UserSerializer,
    }
)
class UpdateAgentProfileView(generics.GenericAPIView):
    serializer_class = (UpdateAgentProfileSerializer)
    permission_classes = (IsOnlyForAgent,)
    parser_classes = (MultiPartParser,)

    def patch(self, request):
        user = request.user
        serializer = self.get_serializer(user.agent_profile, data=request.data, partial=True)

        if serializer.is_valid(raise_exception=True):
            serializer.save()

            return Response(UserSerializer(user).data)


@extend_schema(
    methods=[ 'PATCH', ],
    summary='평카인 정산 계좌 수정',
    description='평카인 정산 계좌 수정 API',
    request=AgentSettlementAccountSerializer,
    responses={
        200: UserSerializer,
    }
)
class UpdateAgentSettlementAccountView(generics.GenericAPIView):
    serializer_class = (AgentSettlementAccountSerializer)
    permission_classes = (IsOnlyForAgent,)

    def patch(self, request):
        user = request.user
        serializer = self.get_serializer(
            getattr(user, 'agent_settlement_account', None),
            data=request.data,
            partial=True,
            context={ 'agent': user, }
        )

        if serializer.is_valid(raise_exception=True):
            serializer.save()

            return Response(UserSerializer(user).data)
