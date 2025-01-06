import json

from rest_framework import serializers

from drf_spectacular.utils import extend_schema_field

from vehicles.models import CarEvaluationSheet

from users.serializers import UserSerializer

from requestings.models import DeliveryResult, RequestingAdditionalCost, \
                                CarBasicImage, CarAccidentSiteImage


class RequestingDeliveryDepartureSerializer(serializers.ModelSerializer):
    type = serializers.CharField()
    number = serializers.CharField(required=False)

    mileage_before_delivery = serializers.IntegerField(min_value=1)

    key_image = serializers.ImageField(required=False)
    dashboard_image = serializers.ImageField(required=False)

    exterior_images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
    )

    interior_images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
    )

    wheel_images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
    )

    basic_images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
    )

    accident_site_images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
    )

    required_document_keys = serializers.ListField(
        child=serializers.CharField(),
        required=False,
    )

    required_document_images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
    )

    etc_images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
    )

    class Meta:
        model = DeliveryResult
        fields = (
            'type',
            'number',
            'mileage_before_delivery',
            'key_image',
            'dashboard_image',
            'exterior_images',
            'interior_images',
            'wheel_images',
            'basic_images',
            'accident_site_images',
            'required_document_keys',
            'required_document_images',
            'etc_images',
        )

    def create(self, validated_data):
        requesting_history = self.context['requesting_history']

        type = validated_data.get('type', None)
        number = validated_data.get('number', None)
        mileage_before_delivery = validated_data['mileage_before_delivery']

        key_image = validated_data.get('key_image', None)
        dashboard_image = validated_data.get('dashboard_image', None)

        exterior_images = validated_data.get('exterior_images', [])
        interior_images = validated_data.get('interior_images', [])
        wheel_images = validated_data.get('wheel_images', [])

        basic_images = validated_data.get('basic_images', [])
        accident_site_images = validated_data.get('accident_site_images', [])

        required_document_keys = validated_data.get('required_document_keys', [])
        required_document_images = validated_data.get('required_document_images', [])

        etc_images = validated_data.get('etc_images', [])

        if type != None:
            requesting_history.car.type = type

        if number != None:
            requesting_history.car.number = number

        delivery_result = DeliveryResult.objects.create(
            requesting_history=requesting_history,
            mileage_before_delivery=mileage_before_delivery,
        )

        requesting_history.car.mileage = mileage_before_delivery
        requesting_history.car.save()

        if key_image is not None:
            CarBasicImage.objects.create(
                delivery_result=delivery_result,
                is_before_delivery=True,
                image=key_image,
                type='CAR_KEY',
            )

        if dashboard_image is not None:
            CarBasicImage.objects.create(
                delivery_result=delivery_result,
                is_before_delivery=True,
                image=dashboard_image,
                type='DASHBOARD',
            )

        for exterior_image in exterior_images:
            CarBasicImage.objects.create(
                delivery_result=delivery_result,
                is_before_delivery=True,
                image=exterior_image,
                type='EXTERIOR',
            )

        for interior_image in interior_images:
            CarBasicImage.objects.create(
                delivery_result=delivery_result,
                is_before_delivery=True,
                image=interior_image,
                type='INTERIOR',
            )

        for wheel_image in wheel_images:
            CarBasicImage.objects.create(
                delivery_result=delivery_result,
                is_before_delivery=True,
                image=wheel_image,
                type='WHEEL',
            )

        for basic_image in basic_images:
            CarBasicImage.objects.create(
                delivery_result=delivery_result,
                is_before_delivery=True,
                image=basic_image,
            )

        for etc_image in etc_images:
            CarBasicImage.objects.create(
                delivery_result=delivery_result,
                is_before_delivery=True,
                image=etc_image,
            )

        for accident_image in accident_site_images:
            CarAccidentSiteImage.objects.create(
                delivery_result=delivery_result,
                is_before_delivery=True,
                image=accident_image,
            )

        for index, document_image in enumerate(required_document_images):
            CarBasicImage.objects.create(
                delivery_result=delivery_result,
                is_before_delivery=True,
                image=document_image,
                type='REQUIRED_DOCUMENTS',
                sub_type=required_document_keys[index],
            )

        return delivery_result


class RequestingDeliveryArriveSerializer(serializers.ModelSerializer):
    mileage_after_delivery = serializers.IntegerField(min_value=1)

    key_image = serializers.ImageField(required=False)
    dashboard_image = serializers.ImageField(required=False)

    exterior_images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
    )

    interior_images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
    )

    wheel_images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
    )

    basic_images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
    )

    accident_site_images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
    )

    etc_images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
    )

    additional_costs = serializers.ListField(
        child=serializers.JSONField(),
        required=False,
    )

    additional_cost_images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
    )

    class Meta:
        model = DeliveryResult
        fields = (
            'mileage_after_delivery',
            'key_image',
            'dashboard_image',
            'exterior_images',
            'interior_images',
            'wheel_images',
            'basic_images',
            'accident_site_images',
            'etc_images',
            'additional_costs',
            'additional_cost_images',
            'memo',
        )

    def update(self, instance, validated_data):
        key_image = validated_data.get('key_image', None)
        dashboard_image = validated_data.get('dashboard_image', None)

        exterior_images = validated_data.get('exterior_images', [])
        interior_images = validated_data.get('interior_images', [])
        wheel_images = validated_data.get('wheel_images', [])

        basic_images = validated_data.get('basic_images', [])
        accident_site_images = validated_data.get('accident_site_images', [])

        additional_costs = validated_data.get('additional_costs', [])
        additional_cost_images = validated_data.get('additional_cost_images', [])

        etc_images = validated_data.get('etc_images', [])

        instance.mileage_after_delivery = validated_data['mileage_after_delivery']

        if instance.mileage_before_delivery > instance.mileage_after_delivery:
            raise serializers.ValidationError({ 'mileage_after_delivery': '주행거리가 출발할때보다 작을 수 없습니다.' })

        instance.memo = validated_data.get('memo')
        instance.save()

        if key_image is not None:
            CarBasicImage.objects.create(
                delivery_result=instance,
                is_before_delivery=False,
                image=key_image,
                type='CAR_KEY',
            )

        if dashboard_image is not None:
            CarBasicImage.objects.create(
                delivery_result=instance,
                is_before_delivery=False,
                image=dashboard_image,
                type='DASHBOARD',
            )

        for exterior_image in exterior_images:
            CarBasicImage.objects.create(
                delivery_result=instance,
                is_before_delivery=False,
                image=exterior_image,
                type='EXTERIOR',
            )

        for interior_image in interior_images:
            CarBasicImage.objects.create(
                delivery_result=instance,
                is_before_delivery=False,
                image=interior_image,
                type='INTERIOR',
            )

        for wheel_image in wheel_images:
            CarBasicImage.objects.create(
                delivery_result=instance,
                is_before_delivery=False,
                image=wheel_image,
                type='WHEEL',
            )

        for basic_image in basic_images:
            CarBasicImage.objects.create(
                delivery_result=instance,
                is_before_delivery=False,
                image=basic_image,
            )

        for etc_image in etc_images:
            CarBasicImage.objects.create(
                delivery_result=instance,
                is_before_delivery=False,
                image=etc_image,
            )

        for accident_image in accident_site_images:
            CarAccidentSiteImage.objects.create(
                delivery_result=instance,
                is_before_delivery=False,
                image=accident_image,
            )

        instance.requesting_history.additional_costs.all().delete()

        for index, raw_additional_cost in enumerate(additional_costs):
            try:
                additional_cost = json.loads(raw_additional_cost)
            except:
                continue

            type = additional_cost.get('type')
            name = additional_cost.get('name')
            cost = additional_cost.get('cost')

            image = None

            try:
                image = additional_cost_images[index]
            except:
                pass

            additional_cost = RequestingAdditionalCost.objects.create(
                requesting_history=instance.requesting_history,
                type=type,
                name=name,
                cost=cost,
                image=image,
            )

        return instance
