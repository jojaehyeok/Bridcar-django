import json

from functools import reduce

from rest_framework import serializers
from rest_framework.exceptions import ParseError

from drf_spectacular.utils import extend_schema_field

from vehicles.models import Car, CarEvaluationResult, CarEvaluationImage


class StartEvaluationSerializer(serializers.ModelSerializer):
    type = serializers.CharField()
    number = serializers.CharField(required=False)
    registration_image = serializers.ImageField()
    instrument_panel_image = serializers.ImageField()
    identification_number_image = serializers.ImageField()

    class Meta:
        model = Car
        fields = ( 'number', 'type', 'registration_image',
                   'instrument_panel_image', 'identification_number_image', )

    def update(self, instance, validated_data):
        instance.type = validated_data.get('type')
        instance.number = validated_data.get('number') or instance.number

        instance.registration_image = validated_data.get('registration_image')
        instance.instrument_panel_image = validated_data.get('instrument_panel_image')
        instance.identification_number_image = validated_data.get('identification_number_image')

        instance.save()

        return instance

class CarEvaluationImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarEvaluationImage
        fields = [ 'uuid', 'image', ]


class CarEvaluationResultSerializer(serializers.ModelSerializer):
    images = CarEvaluationImageSerializer(many=True)

    drivers_side_mirror_cover_marker = serializers.ListField(child=serializers.CharField())
    drivers_side_mirror_mirror_marker = serializers.ListField(child=serializers.CharField())
    drivers_side_mirror_repeater_marker = serializers.ListField(child=serializers.CharField())

    passenger_side_mirror_cover_marker = serializers.ListField(child=serializers.CharField())
    passenger_side_mirror_mirror_marker = serializers.ListField(child=serializers.CharField())
    passenger_side_mirror_repeater_marker = serializers.ListField(child=serializers.CharField())

    class Meta:
        model = CarEvaluationResult
        exclude = [ 'car', ]


class UpdateCarEvaluationResultSerializer(serializers.ModelSerializer):
    color = serializers.CharField(
        allow_blank=True,
    )

    mileage = serializers.IntegerField(
        min_value=0,
        default=0,
        required=False,
    )

    images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
    )

    image_ids = serializers.ListField(child=serializers.CharField())

    class Meta:
        model = CarEvaluationResult
        exclude = [ 'car', ]

    def create(self, validated_data):
        car = self.context['car']

        color = validated_data.get('color', None)
        mileage = validated_data.get('mileage', None)
        images = validated_data.pop('images', [])
        raw_image_ids = validated_data.pop('image_ids', [[]])[0]

        try:
            image_ids = json.loads(raw_image_ids)
        except:
            raise ParseError('INVALID_IMAGE_IDS')

        if color:
            car.color = color

        if mileage:
            car.mileage = mileage

        if color or mileage:
            car.save()

        evaluation_result = CarEvaluationResult.objects.create(
            car=self.context['car'],
            **validated_data,
        )

        if len(images) == len(image_ids):
            CarEvaluationImage.objects.bulk_create(
                [
                    CarEvaluationImage(evaluation_result=evaluation_result, uuid=image_ids[index], image=image)
                        for index, image in enumerate(images)
                ]
            )

        return evaluation_result

    def update(self, obj, validated_data):
        color = validated_data.get('color', None)
        mileage = validated_data.get('mileage', None)
        images = validated_data.pop('images', [])
        raw_image_ids = validated_data.pop('image_ids', [[]])[0]

        try:
            image_ids = json.loads(raw_image_ids)
        except:
            raise ParseError('INVALID_IMAGE_IDS')

        car = obj.car

        if color:
            car.color = color

        if mileage:
            car.mileage = mileage

        if color or mileage:
            car.save()

        CarEvaluationResult.objects.filter(pk=obj.pk) \
            .update(**validated_data)

        if len(images) > 0 and len(images) == len(image_ids):
            obj.images.all().delete()

            CarEvaluationImage.objects.bulk_create(
                [
                    CarEvaluationImage(evaluation_result=obj, uuid=image_ids[index], image=image)
                        for index, image in enumerate(images)
                ]
            )

        return obj
