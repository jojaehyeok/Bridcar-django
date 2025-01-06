from rest_framework import serializers

from .. import models


class UploadCarEvaluationSheetSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.ImageField(
            allow_empty_file=False,
            use_url=False,
        )
    )

    class Meta:
        model = models.CarEvaluationSheet
        fields = ['images',]


    def create(self, validated_data):
        last_evaluation_sheet = None

        images = validated_data.pop('images')

        for image in images:
            last_evaluation_sheet = models.CarEvaluationSheet.objects.create(
                car=self.context['car'],
                image=image,
            )

        return last_evaluation_sheet
