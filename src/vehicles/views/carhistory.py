import json

from asgiref.sync import async_to_sync

from rest_framework import status, generics, mixins, viewsets
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.exceptions import NotFound, PermissionDenied, ParseError

from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer

from vehicles.serializers import UpdateCarEvaluationResultSerializer
from vehicles.models import Car, CarhistoryResult

from requestings.serializers import RequestingHistorySerializer, WorkingRequestingHistorySerializer

from users.permissions import IsOnlyForAgent

from pcar.utils import RedisQueue


@extend_schema(
    summary='카히스토리 스크래핑 하기',
    description='카히스토리 스크래핑 하기 API',
    responses={
        200: RequestingHistorySerializer
    }
)
class StartCarhistoryCrawlingView(generics.GenericAPIView):
    permission_classes = [ IsOnlyForAgent ]

    def get_object(self, pk):
        car = None

        try:
            car = Car.objects.get(pk=pk)
        except Car.DoesNotExist:
            raise NotFound('CAR_NOT_FOUND')

        if car.requesting_history.agent != self.request.user:
            raise PermissionDenied('CAR_NOT_FOUND')

        if car.requesting_history.type != 'EVALUATION_DELIVERY':
            raise PermissionDenied('CAR_NOT_FOUND')

        return car

    def post(self, request, id):
        car = self.get_object(id)

        if not hasattr(car, 'carhistory_result'):
            CarhistoryResult.objects.create(
                car=car,
                is_scrapping=True,
            )
        else:
            carhistory_result = car.carhistory_result

            if carhistory_result.is_scrapping:
                raise ParseError('NOW_SCRAPPING')
            elif not carhistory_result.error_message:
                raise ParseError('ALREADY_SCRAPPED')

            carhistory_result.is_scrapping = True
            carhistory_result.save()

        rq = RedisQueue('carhistory_scraper')

        async_to_sync(rq.put)(json.dumps({
            'requesting_id': car.requesting_history.id,
            'car_number': car.number,
        }))

        return Response(
            WorkingRequestingHistorySerializer(
                car.requesting_history,
                context={ 'user': request.user, }
            ).data
        )
