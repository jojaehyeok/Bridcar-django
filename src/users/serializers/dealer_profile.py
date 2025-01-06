from django.utils import timezone

from rest_framework import serializers
from rest_framework.exceptions import ParseError

from users.models import DealerProfile, SMSAuthenticationHistory

from locations.models import CommonLocation
from locations.serializers import CommonLocationSerializer

from .dealer_company import DealerCompanySerializer


class DealerProfileSerializer(serializers.ModelSerializer):
    company = DealerCompanySerializer()
    main_warehouses = CommonLocationSerializer(many=True)

    class Meta:
        model = DealerProfile
        exclude = [ 'user', ]


class CreateDealerProfileSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    mobile_number = serializers.CharField()
    authentication_code = serializers.CharField()

    main_warehouses = CommonLocationSerializer(
        many=True,
        required=False,
    )

    '''
    require_publish_bill = serializers.BooleanField(
        required=False,
        allow_null=True,
    )
    '''

    class Meta:
        model = DealerProfile
        exclude = [ 'user', ]

    def validate(self, data):
        mobile_number = data.get('mobile_number', None)
        authentication_code = data.get('authentication_code', None)

        if mobile_number != None:
            if authentication_code == None:
                raise ParseError('INVALID_SMS_AUTHENTICATION_CODE')

            now = timezone.now()

            sms_authentication_history = SMSAuthenticationHistory.objects.filter(
                purpose='change_mobile_number',
                mobile_number=mobile_number,
                authentication_code=authentication_code,
                created_at__gte=now - timezone.timedelta(minutes=5),
            ).first()

            if sms_authentication_history == None:
                raise ParseError('FAILED_SMS_AUTHENTICATION')

            data.pop('authentication_code')

        return data

    def create(self, user):
        self.validated_data.pop('name', None)

        #require_publish_bill = self.validated_data.pop('require_publish_bill', False)
        main_warehouses = self.validated_data.pop('main_warehouses', None)

        dealer_profile = DealerProfile.objects.create(
            user=user,
            **self.validated_data,
            #require_publish_bill=require_publish_bill,
        )

        if main_warehouses != None:
            for warehouse in main_warehouses:
                try:
                    warehouse_location = CommonLocation.objects.create(**warehouse)
                except:
                    continue

                dealer_profile.main_warehouses.add(warehouse_location)

        return dealer_profile

    def update(self, instance, validated_data):
        name = validated_data.pop('name', None)
        mobile_number = validated_data.pop('mobile_number', None)
        #require_publish_bill = validated_data.pop('require_publish_bill', instance.require_publish_bill)
        main_warehouses = validated_data.pop('main_warehouses', None)

        #validated_data['require_publish_bill'] = require_publish_bill

        if name != None:
            instance.user.name = name

        if mobile_number != None:
            instance.user.mobile_number = mobile_number

        if name != None or mobile_number != None:
            instance.user.save()

        super(CreateDealerProfileSerializer, self).update(instance, validated_data)

        if main_warehouses != None:
            instance.main_warehouses.all().delete()

            for warehouse in main_warehouses:
                try:
                    warehouse_location = CommonLocation.objects.create(**warehouse)
                except:
                    continue

                instance.main_warehouses.add(warehouse_location)

        return instance


class CreateDealerBusinessRegistrationSerializer(serializers.ModelSerializer):
    business_registration = serializers.ImageField(required=True)

    class Meta:
        model = DealerProfile
        fields = [ 'business_registration', ]
