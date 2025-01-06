from rest_framework import serializers

from requestings.models import ExternalEvaluationTemplate


class ExternalEvaluationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalEvaluationTemplate
        fields = '__all__'
