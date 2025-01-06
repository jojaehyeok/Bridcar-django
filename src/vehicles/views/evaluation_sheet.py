from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_framework.parsers import MultiPartParser
from rest_framework import generics, mixins, viewsets

from requestings.serializers import RequestingHistorySerializer

from vehicles.serializers import UploadCarEvaluationSheetSerializer
from vehicles.models import Car, CarEvaluationSheet

class EvaluationSheetViewSet(viewsets.ModelViewSet):
    serializer_class = UploadCarEvaluationSheetSerializer
    parser_classes = (MultiPartParser,)

    def get_object(self):
        try:
            return CarEvaluationSheet.objects.get(
                car__id=self.kwargs['id'],
            )
        except CarEvaluationSheet.DoesNotExist:
            raise NotFound

    def get_queryset(self):
        return CarEvaluationSheet.objects.filter(
            user=self.request.user
        )

    def get_serializer_context(self):
        context = super(EvaluationSheetViewSet, self).get_serializer_context()

        car_id = self.kwargs.get('id')

        try:
            car = Car.objects.get(id=car_id)
            context['car'] = car
        except Car.DoesNotExist:
            raise NotFound

        return context

    def create(self, request, *args, **kwargs):
        serializer_context = self.get_serializer_context()

        CarEvaluationSheet.objects.filter(car__id=self.kwargs.get('id')) \
            .delete()

        save_serializer = UploadCarEvaluationSheetSerializer(
            data=request.data,
            context=self.get_serializer_context(),
        )

        if save_serializer.is_valid(raise_exception=True):
            save_serializer.save()

            return Response(RequestingHistorySerializer(serializer_context['car'].requesting_history).data)

    def destroy(self, request, *args, **kwargs):
        super(EvaluationSheetViewSet, self).destroy(request, *args, **kwargs)

        serializer_context = self.get_serializer_context()

        return Response(RequestingHistorySerializer(serializer_context['car'].requesting_history).data)
