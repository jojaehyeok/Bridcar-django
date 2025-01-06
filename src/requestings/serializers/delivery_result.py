from rest_framework import serializers

from drf_spectacular.utils import extend_schema_field

from requestings.models import DeliveryResult


class RequiredDocumentSerializer(serializers.Serializer):
    key = serializers.CharField()
    image_urls = serializers.ListField(child=serializers.URLField())


class DeliveryResultSerializer(serializers.ModelSerializer):
    basic_images_before_delivery = serializers.SerializerMethodField()
    accident_site_images_before_delivery = serializers.SerializerMethodField()

    basic_images_after_delivery = serializers.SerializerMethodField()
    accident_site_images_after_delivery = serializers.SerializerMethodField()

    required_documents = serializers.SerializerMethodField()

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_basic_images_before_delivery(self, obj):
        return map(
            lambda x: x.image.url,
            obj.car_basic_images \
                .filter(is_before_delivery=True) \
                .exclude(type='REQUIRED_DOCUMENTS')
        )

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_accident_site_images_before_delivery(self, obj):
        return map(lambda x: x.image.url, obj.car_accident_site_images.filter(is_before_delivery=True))

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_basic_images_after_delivery(self, obj):
        return map(lambda x: x.image.url, obj.car_basic_images.filter(is_before_delivery=False))

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_accident_site_images_after_delivery(self, obj):
        return map(lambda x: x.image.url, obj.car_accident_site_images.filter(is_before_delivery=False))

    @extend_schema_field(serializers.ListField(child=RequiredDocumentSerializer()))
    def get_required_documents(self, obj):
        document_images = obj.car_basic_images.filter(type='REQUIRED_DOCUMENTS')
        document_images_dict = {}

        for document_image in document_images:
            if document_images_dict.get(document_image.sub_type, None) is None:
                document_images_dict[document_image.sub_type] = [ document_image.image.url ]
            else:
                document_images_dict[document_image.sub_type].append(document_image.image.url)

        return RequiredDocumentSerializer(
            [ { 'key': entry[0], 'image_urls': entry[1], } for entry in document_images_dict.items() ],
            many=True,
        ).data

    class Meta:
        model = DeliveryResult
        exclude = [ 'id', 'requesting_history', ]
