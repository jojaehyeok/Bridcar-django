from django.db.models import Q

from rest_framework import filters, generics, mixins, status, serializers
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.exceptions import ParseError, NotFound

from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer

from boards.models import Agreement
from boards.serializers import AgreementSerializer
from boards.constants import AGREEMENT_TYPES


@extend_schema(
    methods=[ 'GET', ],
    summary='이용약관 가져오기',
    description='이용약관 가져오기 API',
    parameters=[
        OpenApiParameter(
            name='type',
            location=OpenApiParameter.QUERY,
            description=', '.join(filter(lambda key: key != 'daily', dict(AGREEMENT_TYPES).keys())),
            required=True,
            type=str
        ),
        OpenApiParameter(
            name='content_only',
            location=OpenApiParameter.QUERY,
            description='컨텐츠만 보기',
            required=False,
            type=str
        ),
    ],
    responses={
        200: AgreementSerializer,
    }
)
class ListAgreementView(generics.GenericAPIView):
    permission_classes = (AllowAny,)

    def get_object(self, agreement_type):
        try:
            return Agreement.objects.get(type=agreement_type)
        except Agreement.DoesNotExist:
            raise NotFound('AGREEMENT_NOT_FOUND')

    def get(self, request):
        agreement_type = request.query_params.get('type')
        content_only = request.query_params.get('content_only')

        agreement = self.get_object(agreement_type)

        return Response(AgreementSerializer(agreement).data)


@extend_schema(
    methods=[ 'GET', ],
    summary='이용약관 디테일 가져오기',
    description='이용약관 디테일 가져오기 API',
    responses={
        200: serializers.CharField(),
    }
)
class AgreementDetailView(generics.GenericAPIView):
    permission_classes = (AllowAny,)
    renderer_classes = [ TemplateHTMLRenderer ]
    template_name = 'boards/agreement.html'

    def get_object(self, agreement_type):
        try:
            return Agreement.objects.get(type=agreement_type)
        except Agreement.DoesNotExist:
            raise NotFound('AGREEMENT_NOT_FOUND')

    def get(self, request, type):
        agreement = self.get_object(type)

        return Response(
            { 'agreement': agreement.content },
        )
