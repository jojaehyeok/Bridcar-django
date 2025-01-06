from rest_framework import serializers

from vehicles.models import CarhistoryResult, CarhistoryAccidentInsuranceHistory, \
                            CarhistoryOwnerChangeHistory


class CarhistoryAccidentInsuranceHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CarhistoryAccidentInsuranceHistory
        exclude = [ 'id', ]


class CarhistoryOwnerChangeHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CarhistoryOwnerChangeHistory
        exclude = [ 'id', 'carhistory_result', ]


class CarhistoryResultSerializer(serializers.ModelSerializer):
    insurance_with_my_damages = CarhistoryAccidentInsuranceHistorySerializer(many=True)
    insurance_with_opposite_damages = CarhistoryAccidentInsuranceHistorySerializer(many=True)
    owner_change_histories = CarhistoryOwnerChangeHistorySerializer(many=True)

    class Meta:
        model = CarhistoryResult
        exclude = [ 'id', 'car', ]
