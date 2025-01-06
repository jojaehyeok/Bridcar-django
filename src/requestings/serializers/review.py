from rest_framework import serializers

from drf_spectacular.utils import extend_schema_field

from users.serializers import UserSerializer

from requestings.models import Review, ReviewImage


class ReviewSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()

    @extend_schema_field(serializers.CharField())
    def get_name(self, obj):
        if obj.requesting_history != None and obj.requesting_history.client != None:
            name = obj.requesting_history.client.name

            return name[0] + ('*' * (len(name) - 1))

        if obj.name != None:
            return obj.name[0] + ('*' * (len(obj.name) - 1))

        return '리뷰 작성자'

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_images(self, obj):
        try:
            return list(map(lambda x: x.image.url, obj.images.all()))
        except:
            return []

    class Meta:
        model = Review
        fields = [ 'name', 'content', 'images', ]


class CreateReviewSerializer(serializers.ModelSerializer):
    images = serializers.ListField(child=serializers.ImageField())

    def create(self, validated_data):
        requesting_history = self.context['requesting_history']

        images = validated_data.get('images', None)

        review = Review.objects.create(
            requesting_history=requesting_history,
            content=validated_data['content'],
        )

        for image in images:
            ReviewImage.objects.create(
                review=review,
                image=image,
            )

        return review


    class Meta:
        model = Review
        fields = [ 'content', 'images', ]
