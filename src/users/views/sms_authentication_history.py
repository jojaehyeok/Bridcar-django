import random

from django.utils import timezone

from rest_framework import generics, mixins, status, serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import ParseError, NotFound, AuthenticationFailed

from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer

from users.models import User, SMSAuthenticationHistory
from users.serializers import RequestSMSAuthenticationSerializer


@extend_schema(
    summary='문자인증 요청',
    description='문자인증 요청 APi',
    request=RequestSMSAuthenticationSerializer,
    responses={
        400: inline_serializer(
            name='RequestSMSAuthenticationErrorSerializer',
            fields={
                'detail': serializers.ChoiceField(
                    help_text=(
                        'USER_NOT_FOUND: 가입된 유저 없음<br/>',
                        'DUPLICATED_MOBILE_NUMBER: 중복된 핸드폰 번호<br/>'
                    ),
                    choices={
                        'USER_NOT_FOUND': '가입된 유저 없음',
                        'DUPLICATED_MOBILE_NUMBER': '중복된 핸드폰 번호',
                    }
                ),
            }
        )
    }
)
class RequestSMSAuthenticationView(generics.GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = (RequestSMSAuthenticationSerializer)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            now = timezone.now()

            purpose = serializer.validated_data['purpose']
            mobile_number = serializer.validated_data['mobile_number']

            exists_sms_history = SMSAuthenticationHistory.objects \
                .filter(
                    purpose=purpose,
                    mobile_number=mobile_number,
                    created_at__gte=now - timezone.timedelta(seconds=5),
                ) \
                .first()

            if exists_sms_history != None:
                return Response(None)

            trying_signin_account = None

            if purpose == 'signup':
                exists_user = User.objects.filter(mobile_number=mobile_number).first()

                if exists_user != None:
                    raise ParseError('DUPLICATED_MOBILE_NUMBER')
            else:
                trying_signin_account = User.objects.filter(mobile_number=mobile_number).first()

                if trying_signin_account == None:
                    raise ParseError('USER_NOT_FOUND')

            without_alimtalk = False

            if purpose == 'signin' and trying_signin_account.is_test_account == True:
                without_alimtalk = True
                authentication_code = '999999'
            else:
                authentication_code = ''.join([str(random.randint(0, 999)).zfill(3) for _ in range(2)])

            SMSAuthenticationHistory.objects.create(
                purpose=purpose,
                mobile_number=mobile_number,
                authentication_code=authentication_code,
                without_alimtalk=without_alimtalk,
            )

            return Response(None)
