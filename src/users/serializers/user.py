import hmac
import hashlib
import binascii

from django.conf import settings
from django.utils import timezone

from rest_framework import serializers
from rest_framework.exceptions import ParseError, PermissionDenied

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

from drf_spectacular.utils import extend_schema_field, inline_serializer

from users.models import User, Agent, SMSAuthenticationHistory, DealerProfile, DealerCompany, AgentProfile

from .agent_profile import AgentProfileSerializer
from .dealer_profile import DealerProfileSerializer
from .agent_profile import AgentSettlementAccountSerializer
from .agent_location import AgentLocationSerializer
from .withdrawal_requesting import WithdrawlRequestingSerializer
from .toss_virtual_account import TossVirtualAccountSerializer


class DealerSignupSerializer(serializers.ModelSerializer):
    authentication_code = serializers.CharField(
        max_length=6,
        help_text='인증번호'
    )

    company_code = serializers.CharField(
        help_text='회사 코드',
        allow_blank=True,
        allow_null=True,
        required=False,
    )

    company_name = serializers.CharField(
        help_text='사업자 등록번호',
        allow_blank=True,
        allow_null=True,
        required=False,
    )

    company_business_registration_number = serializers.CharField(
        help_text='사업자 등록번호',
        allow_blank=True,
        allow_null=True,
        required=False,
    )

    referer_user_id = serializers.CharField(
        allow_blank=True,
        allow_null=True,
        required=False,
    )

    class Meta:
        model = User
        fields = (
            'name', 'mobile_number', 'authentication_code', 'company_code', 'company_name', \
            'company_business_registration_number', 'referer_user_id',
        )

    def validate(self, validated_data):
        now = timezone.now()

        mobile_number = validated_data['mobile_number']
        authentication_code = validated_data['authentication_code']

        company_code = validated_data.get('company_code')

        sms_authentication_history = SMSAuthenticationHistory.objects.filter(
            purpose='signup',
            mobile_number=mobile_number,
            authentication_code=authentication_code,
            created_at__gte=now - timezone.timedelta(minutes=10),
        ).first()

        if sms_authentication_history == None:
            raise ParseError('FAILED_SMS_AUTHENTICATION')

        if company_code:
            company = DealerCompany.objects.filter(id=company_code).first()

            if not company:
                raise ParseError('INVALID_COMPANY_CODE')

            validated_data['company'] = company

        if validated_data.get('referer_user_id', None):
            try:
                validated_data['referer_user'] = \
                    Agent.objects.get(pk=validated_data['referer_user_id'])
            except Agent.DoesNotExist:
                raise serializers.ValidationError('INVALID_REFERER')

        return validated_data

    def create(self, validated_data):
        company = validated_data.get('company')
        company_name = validated_data.get('company_name')
        company_business_registration_number = validated_data.get('company_business_registration_number')

        referer_user = validated_data.get('referer_user', None)

        user = User(
            name=validated_data['name'],
            mobile_number=validated_data['mobile_number'],
            referer=referer_user,
        )

        user.save()

        if referer_user != None:
            if referer_user.is_agent:
                referer_user.agent_profile.total_marketing_count += 1
                referer_user.agent_profile.save()

        if company_name and company_business_registration_number:
            company = DealerCompany.objects.create(
                name=company_name,
                business_registration_number=company_business_registration_number,
            )

        if company:
            DealerProfile.objects.create(
                user=user,
                company=company,
            )
        else:
            DealerProfile.objects.create(user=user)

        return user


class AgentSignupSerializer(serializers.ModelSerializer):
    authentication_code = serializers.CharField(
        max_length=6,
        help_text='인증번호'
    )

    profile_image = serializers.ImageField()

    '''
    referer = serializers.CharField(
        allow_null=True,
        required=False,
    )
    '''

    class Meta:
        model = User
        fields = ( 'name', 'mobile_number', 'authentication_code', 'profile_image', )

    def validate(self, validated_data):
        now = timezone.now()

        mobile_number = validated_data['mobile_number']
        authentication_code = validated_data['authentication_code']

        sms_authentication_history = SMSAuthenticationHistory.objects.filter(
            purpose='signup',
            mobile_number=mobile_number,
            authentication_code=authentication_code,
            created_at__gte=now - timezone.timedelta(minutes=5),
        ).first()

        if sms_authentication_history == None:
            raise PermissionDenied('FAILED_SMS_AUTHENTICATION')

        '''
        if validated_data.get('referer'):
            try:
                validated_data['referer_user'] = \
                    models.User.objects.get(username=validated_data['referer'])
            except models.User.DoesNotExist:
                raise serializers.ValidationError('INVALID_REFERER')
        '''

        return validated_data

    def create(self, validated_data):
        user = User(
            name=validated_data['name'],
            mobile_number=validated_data['mobile_number'],
        )

        '''
        if validated_data.get('referer_user') and validated_data['referer_user'].profile:
            validated_data['referer_user'].profile.item_count += constants.ITEM_GIVING_COUNT['referer_reward']
            validated_data['referer_user'].profile.save()

            user.referer = validated_data['referer_user']
        '''

        user.save()

        AgentProfile.objects.create(
            user=user,
            profile_image=validated_data['profile_image'],
        )

        return user


class SigninSerializer(serializers.Serializer):
    role = serializers.ChoiceField(
        required=False,
        choices=(
            ('agent', '평카인'),
            ('dealer', '딜러'),
            ('control_room', '상황실'),
        ),
    )

    mobile_number = serializers.CharField(required=True)
    authentication_code = serializers.CharField(required=True)


class UserForNotificationSerializer(serializers.ModelSerializer):
    agent_profile = AgentProfileSerializer(read_only=True)
    dealer_profile = DealerProfileSerializer(read_only=True)

    class Meta:
        model = User
        exclude = [
            'last_login', 'is_active', 'is_superuser',
            'password', 'groups', 'user_permissions', 'created_at',
        ]


class UserSerializer(serializers.ModelSerializer):
    agent_profile = AgentProfileSerializer(read_only=True)
    agent_settlement_account = AgentSettlementAccountSerializer(read_only=True)
    agent_location = AgentLocationSerializer(read_only=True)
    dealer_profile = DealerProfileSerializer(read_only=True)
    processing_withdrawals = serializers.SerializerMethodField()
    channel_talk_member_hash = serializers.SerializerMethodField()
    virtual_account = serializers.SerializerMethodField()

    class Meta:
        model = User
        exclude = [
            'last_login', 'is_active', 'is_superuser',
            'password', 'groups', 'user_permissions', 'created_at',
        ]

    @extend_schema_field(WithdrawlRequestingSerializer(many=True))
    def get_processing_withdrawals(self, obj):
        return WithdrawlRequestingSerializer(obj.withdrawal_requestings.filter(is_processed=False), many=True).data

    @extend_schema_field(serializers.CharField())
    def get_channel_talk_member_hash(self, obj):
        return hmac.new(
            binascii.unhexlify(bytearray(settings.CHANNEL_TALK_MEMBER_SECRET_KEY, "utf-8")),
            msg=str(obj.id).encode('utf-8'),
            digestmod=hashlib.sha256
        ).hexdigest()

    @extend_schema_field(TossVirtualAccountSerializer())
    def get_virtual_account(self, obj):
        if obj.processing_virtual_account != None:
            return TossVirtualAccountSerializer(obj.processing_virtual_account).data

        return None

    def to_representation(self, obj):
        user = self.context.get('user')
        fields = super(UserSerializer, self).to_representation(obj)

        if user:
            if not hasattr(user, 'agent_profile'):
                del fields['dealer_profile']
                del fields['virtual_account']
            elif not hasattr(user, 'dealer_profile'):
                del fields['agent_profile']

        return fields


class AgentSerializer(serializers.ModelSerializer):
    agent_profile = AgentProfileSerializer(read_only=True)
    agent_settlement_account = AgentSettlementAccountSerializer(read_only=True)
    agent_location = AgentLocationSerializer(read_only=True)
    is_working = serializers.SerializerMethodField()

    def get_is_working(self, obj):
        if not hasattr(obj, 'agent_location'):
            return False

        now = timezone.now()

        return obj.agent_location.updated_at > (now - timezone.timedelta(hours=1))

    class Meta:
        model = User
        exclude = [
            'last_login', 'is_active', 'is_superuser',
            'password', 'groups', 'user_permissions', 'created_at',
        ]

class AgentForAdminSerializer(AgentSerializer):
    currently_working_requesting = serializers.SerializerMethodField()

    @extend_schema_field(inline_serializer(
        name='SimpleRequestingHistorySerializerForAdmin',
        fields={
            'id': serializers.CharField(),
            'source_address': serializers.CharField(),
            'destination_address': serializers.CharField(),
        }
    ))
    def get_currently_working_requesting(self, obj):
        result = {}
        working_requesting = obj.currently_working_requesting

        if working_requesting != None:
            try:
                result['id'] = working_requesting.pk
                result['source_address'] = f'{ working_requesting.source_location.road_address } { working_requesting.source_location.detail_address }'
                result['destination_address'] = f'{ working_requesting.destination_location.road_address } { working_requesting.destination_location.detail_address }'
            except:
                pass

            return result

        return None

class SignupSuccessSerializer(serializers.Serializer):
    user = UserSerializer(read_only=True)
    access_token = serializers.CharField(label='엑세스 토큰', read_only=True)

    class Meta:
        model = User

    def to_representation(self, instance):
        refresh = RefreshToken.for_user(instance)

        return {
            'user': UserSerializer(instance).data,
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
        }


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    refresh = None
    access = None
    refresh_token = serializers.CharField()
    access_token = serializers.CharField(read_only=True)

    def validate(self, attrs):
        refresh = self.token_class(attrs['refresh_token'])

        data = {'access_token': str(refresh.access_token)}

        if api_settings.ROTATE_REFRESH_TOKENS:
            if api_settings.BLACKLIST_AFTER_ROTATION:
                try:
                    refresh.blacklist()
                except AttributeError:
                    pass

            refresh.set_jti()
            refresh.set_exp()
            refresh.set_iat()

            data['refresh_token'] = str(refresh)

        return data
