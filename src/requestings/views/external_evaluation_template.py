from rest_framework import generics, mixins, status, serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.exceptions import ParseError, NotFound, AuthenticationFailed

from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer

from users.permissions import IsOnlyForAgent

from vehicles.models import Car

from requestings.models import ExternalEvaluationTemplate
from requestings.serializers import ExternalEvaluationTemplateSerializer


@extend_schema(
    summary='외부 평가지 목록 가져오기',
    description='외부 평가지 목록 가져오게 API',
)
class ListExternalEvaluationTemplatesView(generics.ListAPIView):
    permission_classes = [ IsOnlyForAgent ]
    serializer_class = ExternalEvaluationTemplateSerializer

    def get_queryset(self):
        return ExternalEvaluationTemplate.objects.filter()
