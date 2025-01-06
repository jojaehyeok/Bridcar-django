from django.utils import timezone
from django.contrib.gis.geos.geometry import GEOSGeometry

from rest_framework import generics, mixins, status, serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import ParseError, NotFound, AuthenticationFailed

from geopy.geocoders import Nominatim

from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer

from users.models import User
from users.permissions import IsOnlyForAgent
from users.serializers import UserSerializer, AgentCurrentLocationSerializer, \
                                AgentLocationConfigSerializer

@extend_schema(
    summary='평카인 현재 위치 기록하기',
    description='평카인 현재 위치 기록하기 API',
    request=AgentCurrentLocationSerializer,
    responses={
        200: UserSerializer,
    }
)
class AgentCurrentLocationView(generics.GenericAPIView):
    permission_classes = (IsOnlyForAgent,)
    serializer_class = (AgentCurrentLocationSerializer)

    def post(self, request):
        user = request.user
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            latitude = serializer.validated_data['latitude']
            longitude = serializer.validated_data['longitude']

            user.agent_location.coord = GEOSGeometry(f'POINT({ longitude } { latitude })', srid=4326)
            user.agent_location.updated_at = timezone.now()

            if user.agent_location.is_end_of_work == True:
                user.agent_location.is_end_of_work = False

            user.agent_location.save()

            return Response(UserSerializer(user).data)


@extend_schema(
    summary='평카인 위치 관련 설정',
    description='평카인 위치 관련 설정 API',
    request=AgentLocationConfigSerializer,
    responses={
        200: UserSerializer,
    }
)
class ConfigLocationView(generics.GenericAPIView):
    permission_classes = (IsOnlyForAgent,)
    serializer_class = (AgentLocationConfigSerializer)

    def patch(self, request):
        user = request.user
        serializer = self.get_serializer(user.agent_location, data=request.data, partial=True)

        if serializer.is_valid(raise_exception=True):
            serializer.save()

            return Response(UserSerializer(user).data)


@extend_schema(
    summary='평카인 업무 종료',
    description='평카인 업무 종료 API',
)
class AgentEndWorkingView(generics.GenericAPIView):
    permission_classes = (IsOnlyForAgent,)

    def delete(self, request):
        user = request.user

        if user.agent_location:
            user.agent_location.is_end_of_work = True
            user.agent_location.save()

        return Response(status=status.HTTP_204_NO_CONTENT)
