from typing import Generic

from django.db.models import Q
from django.utils import timezone

from rest_framework import generics, mixins, status, serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.exceptions import ParseError, NotFound, AuthenticationFailed, PermissionDenied

from rest_framework_simplejwt.tokens import RefreshToken

from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer

from rest_framework_simplejwt.views import TokenRefreshView

from users.models import User

from daangn.serializers import IssueTokenSerializer, IssuedTokenResultSerializer


@extend_schema(
    methods=[ 'POST', ],
    summary='토큰 발급',
    description='토큰 발급 API',
    request=IssueTokenSerializer,
    responses={
        200: IssuedTokenResultSerializer,
    }
)
class IssueTokenView(generics.GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = IssueTokenSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            api_id = serializer.validated_data['api_id']
            api_secret = serializer.validated_data['api_secret']

            try:
                user = User.objects.get(api_id=api_id, api_secret=api_secret)

                refresh = RefreshToken.for_user(user)
                response_serializer = IssuedTokenResultSerializer({
                    'access_token': refresh.access_token,
                    'refresh_token': str(refresh)
                })

                return Response(response_serializer.data)
            except User.DoesNotExist:
                raise ParseError('INVALID_API_CREDENTIAL')
