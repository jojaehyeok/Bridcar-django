from rest_framework import status, generics, mixins, viewsets
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.exceptions import NotFound, PermissionDenied

from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer

from vehicles.serializers import UpdateCarEvaluationResultSerializer
from vehicles.models import Car, CarEvaluationSheet

from requestings.serializers import RequestingHistorySerializer

from users.permissions import IsOnlyForAgent


@extend_schema(
    summary='평카 내용 저장',
    description='평카 내용 저장 API',
    request=UpdateCarEvaluationResultSerializer,
    responses={
        200: RequestingHistorySerializer
    }
)
class SaveCarEvaluationResultView(generics.GenericAPIView):
    permission_classes = [ IsOnlyForAgent ]
    serializer_class = UpdateCarEvaluationResultSerializer
    parser_classes = (MultiPartParser,)

    def get_object(self, pk):
        car = None

        try:
            car = Car.objects.get(pk=pk)
        except Car.DoesNotExist:
            raise NotFound('CAR_NOT_FOUND')

        if car.requesting_history.agent != self.request.user:
            raise PermissionDenied('CAR_NOT_FOUND')

        return car

    def patch(self, request, id):
        car = self.get_object(id)

        serializer = self.get_serializer(
            getattr(car, 'evaluation_result', None),
            data=request.data,
            context={ 'car': car, },
        )

        if serializer.is_valid(raise_exception=True):
            serializer.save()

            return Response(RequestingHistorySerializer(car.requesting_history).data)
