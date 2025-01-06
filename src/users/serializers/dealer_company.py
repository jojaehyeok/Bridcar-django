from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from users.models import DealerCompany


class DealerCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = DealerCompany
        fields = [ 'id', 'name', 'business_registration_number', 'person_in_charge_number', ]
