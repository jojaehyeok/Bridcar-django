from rest_framework import serializers

from boards.models import Agreement


class AgreementListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agreement
        fields = ('id', 'name',)


class AgreementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agreement
        fields = '__all__'
