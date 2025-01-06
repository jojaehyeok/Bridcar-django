from typing import Generic

from django.db.models import Q
from django.utils import timezone

from rest_framework import generics, mixins, status, serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.exceptions import ParseError, NotFound, AuthenticationFailed, PermissionDenied

from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer

from rest_framework_simplejwt.views import TokenRefreshView

from users.models import User, Agent, SMSAuthenticationHistory, sms_authentication_history
from users.permissions import IsOnlyControlRoomUser
from users.serializers import DealerSignupSerializer, AgentSerializer, SigninSerializer, \
                                SignupSuccessSerializer, UserSerializer, CustomTokenRefreshSerializer, \
                                AgentForAdminSerializer

@extend_schema(
    summary='딜러 회원가입',
    description='딜러 회원가입 API',
    request=DealerSignupSerializer,
    responses={
        200: SignupSuccessSerializer,
        400: inline_serializer(
            name='SignupErrorSerializer',
            fields={
                'detail': serializers.ChoiceField(
                    help_text=( 'DUPLICATED_USERNAME: 중복된 유저 에러<br/>'
                                'FAILED_SMS_AUTHENTICATION: 문자 인증 실패' ),
                    choices={
                        'DUPLICATED_USERNAME': '중복된 유저 ID',
                        'FAILED_SMS_AUTHENTICATION': '문자 인증 실패',
                    }
                ),
            }
        )
    }
)
class DealerSignupView(generics.GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = (DealerSignupSerializer)

    def post(self, request):
        now = timezone.now()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            user = serializer.save()

            return Response(SignupSuccessSerializer(user).data)


@extend_schema(
    summary='로그인',
    description='로그인 API',
    request=SigninSerializer,
    responses={
        200: SignupSuccessSerializer,
        400: inline_serializer(
            name='로그인 에러',
            fields={
                'detail': serializers.ChoiceField(
                    help_text=( 'INVALID_USER: 등록되지 않은 계정<br/>'
                                'INVALID_AUTHENTICATION_CODE: 올바르지 않은 인증번호' ),
                    choices={
                        'INVALID_USER': '등록되지 않은 계정',
                        'INVALID_AUTHENTICATION_CODE': '올바르지 않은 인증번호',
                    }
                ),
            }
        )
    }
)
class SigninView(generics.GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = (SigninSerializer)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        role = serializer.validated_data['role']

        users = User.objects \
            .prefetch_related('agent_profile') \
            .prefetch_related('dealer_profile') \
            .filter(
                mobile_number=serializer.validated_data['mobile_number'],
                is_active=True,
            )

        if role == 'agent':
            users = users.filter(agent_profile__isnull=False)
        elif role == 'dealer':
            users = users.filter(dealer_profile__isnull=False)

        if role != 'control_room':
            if len(users) == 0:
                raise ParseError('INVALID_USER')
            elif len(users) > 1:
                raise ParseError('MORE_THAN_ONE_USERS')

        user = users[0]

        if role == 'control_room':
            if not user.check_authentication_code(
                    serializer.validated_data['authentication_code'], purpose='control_room_signin'):
                raise ParseError('INVALID_AUTHENTICATION_CODE')
        else:
            if not user.check_authentication_code(serializer.validated_data['authentication_code']):
                raise ParseError('INVALID_AUTHENTICATION_CODE')

        if role == 'agent':
            if not hasattr(user, 'agent_profile'):
                raise ParseError('INVALID_ROLE')
        elif role == 'dealer':
            if not hasattr(user, 'dealer_profile'):
                raise ParseError('INVALID_ROLE')
        elif role == 'control_room':
            if not user.is_superuser:
                raise PermissionDenied('INVALID_ROLE')

        return Response(SignupSuccessSerializer(user).data)


@extend_schema(
    methods=[ 'GET', ],
    summary='유저 정보 가져오기',
    description='유저 정보 가져오기 API',
    request=SigninSerializer,
    responses={
        200: UserSerializer,
    }
)
@extend_schema(
    methods=[ 'DELETE', ],
    summary='로그아웃',
    description='로그아웃 API',
)
class UserSelfDetailView(generics.GenericAPIView):
    def get_object(self):
        return User.objects \
                    .prefetch_related('agent_profile') \
                    .prefetch_related('dealer_profile') \
                    .get(pk=self.request.user.id)

    def get(self, request):
        user = self.get_object()

        return Response(UserSerializer(user).data)

    def delete(self, request):
        request.user.fcmdevice_set.all().delete()

        return Response(None)


@extend_schema(
    summary='평카인 목록 (상황실 전용)',
    description='평카인 목록 API',
    parameters=[
        OpenApiParameter(
            name='include_end_of_work',
            location=OpenApiParameter.QUERY,
            description='영업 종료된 평카인 포함',
            required=False,
            type=bool
        ),
    ],
    responses={
        200: UserSerializer(many=True),
    }
)
class AgentListView(generics.ListAPIView):
    serializer_class = (AgentForAdminSerializer)
    permission_classes = (IsOnlyControlRoomUser,)
    pagination_class = None

    def get_queryset(self):
        now = timezone.now()

        search_value = self.request.query_params.get('search_value', None)
        include_end_of_work = self.request.query_params.get('include_end_of_work', None)

        queryset = Agent.objects.filter(
            Q(agent_profile__isnull=False)& \
            Q(agent_location__isnull=False)& \
            Q(agent_location__coord__isnull=False)
        )

        if include_end_of_work == 'false':
            queryset = queryset.exclude(
                Q(agent_location__updated_at__lt=(now - timezone.timedelta(hours=1)))| \
                Q(agent_location__is_end_of_work=True)
            )

        if search_value:
            try:
                integer_search_value = int(search_value, 10)

                queryset = queryset.filter(
                    Q(name__contains=search_value)| \
                    Q(agent_profile__id=integer_search_value)
                )
            except:
                queryset = queryset.filter(
                    Q(name__contains=search_value)
                )

        return queryset

    def get(self, request, *args, **kwargs):
        return super(AgentListView, self).list(self, request, *args, **kwargs)


@extend_schema(
    summary='회원탈퇴',
    description='회원탈퇴 API',
)
class SignoutView(generics.GenericAPIView):
    def delete(self, request):
        if hasattr(request.user, 'agent_profile'):
            raise PermissionDenied('AGENT_CANNOT_SIGNOUT')

        request.user.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    summary='토큰 리프레쉬',
    description='토큰 리프레쉬 API',
    request=CustomTokenRefreshSerializer,
)
class TokenRefreshView(TokenRefreshView):
    serializer_class = (CustomTokenRefreshSerializer)
