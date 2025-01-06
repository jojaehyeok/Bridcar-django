from rest_framework import generics, mixins, status, serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.exceptions import ParseError, NotFound, AuthenticationFailed

from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer

from users.permissions import IsOnlyForDealer

from vehicles.models import Car

from requestings.models import ExternalEvaluationTemplate
from requestings.serializers import UploadBulkRequestingSerializer

from notifications.models import Notification


@extend_schema(
    summary='다량 발주 업로드',
    description='다량 벌주 업로드 API',
)
class UploadBulkRequestingView(generics.GenericAPIView):
    permission_classes = [ IsOnlyForDealer ]
    serializer_class = UploadBulkRequestingSerializer
    parser_classes = [ MultiPartParser, ]

    def post(self, request):
        serializer = self.get_serializer(data=request.data, context={ 'client': request.user, })

        if serializer.is_valid(raise_exception=True):
            serializer.save()

            Notification.create(
                'CONTROL_ROOM',
                'CREATE_BULK_REQUESTING',
                user=None,
                actor=request.user,
                send_fcm=False
            )

            return Response(None)
