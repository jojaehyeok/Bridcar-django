from rest_framework import serializers

from users.models import SMSAuthenticationHistory

class RequestSMSAuthenticationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SMSAuthenticationHistory
        fields = [ 'purpose', 'mobile_number', ]
