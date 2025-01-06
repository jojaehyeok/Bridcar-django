from django.db.models import Q

from rest_framework import status, generics, mixins, viewsets
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.exceptions import NotFound, PermissionDenied

from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer

from vehicles.serializers import UpdatePerformanceCheckRecordsSerializer
from vehicles.models import Car, PerformanceCheckRecord

from requestings.serializers import RequestingHistorySerializer

from users.permissions import IsOnlyForDealer


@extend_schema(
    summary='성능점검기록부 업로드',
    description='성능점검기록부 업로드 API',
    request=UpdatePerformanceCheckRecordsSerializer,
    responses={
        200: RequestingHistorySerializer
    }
)
class PerformanceCheckRecordsView(generics.GenericAPIView):
    permission_classes = [ IsOnlyForDealer ]
    serializer_class = UpdatePerformanceCheckRecordsSerializer
    parser_classes = (MultiPartParser,)

    def patch(self, request, id):
        try:
            car = Car.objects.get(
                Q(pk=id)& \
                Q(requesting_history__client=request.user)
            )
        except Car.DoesNotExist:
            raise NotFound('INVALID_CAR')

        if car.requesting_history.type != 'EVALUATION_DELIVERY' or \
                (car.requesting_history.status != 'DELIVERING_DONE' and \
                car.requesting_history.status != 'DONE'):
            raise PermissionDenied('INVALID_REQUESTING_STATUS')

        serializer = self.get_serializer(
            data=request.data,
            context={ 'car': car, },
        )

        if serializer.is_valid(raise_exception=True):
            serializer.save()

            return Response(RequestingHistorySerializer(car.requesting_history).data)
