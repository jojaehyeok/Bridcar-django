from django.db.models import Q

from rest_framework import generics, mixins, status, serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.exceptions import ParseError, NotFound, AuthenticationFailed, PermissionDenied

from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer

from users.permissions import IsOnlyForAgent, IsOnlyForDealer

from requestings.models import RequestingHistory, Review
from requestings.serializers import ReviewSerializer, RequestingHistorySerializer, CreateReviewSerializer


@extend_schema(
    summary='의뢰 리뷰 작성',
    description='의뢰 리뷰 작성 API (의뢰인)',
    request=CreateReviewSerializer,
    responses=RequestingHistorySerializer,
)
class WriteRequestingReviewView(generics.GenericAPIView):
    parser_classes = [ MultiPartParser, ]
    permission_classes = [ IsOnlyForDealer, ]
    serializer_class = CreateReviewSerializer

    def get_object(self, pk):
        user = self.request.user

        try:
            return RequestingHistory.objects.get(
                pk=pk,
                client=user,
            )
        except RequestingHistory.DoesNotExist:
            raise NotFound

    def post(self, request, id):
        user = request.user
        requesting_history = self.get_object(id)

        if requesting_history.status != 'DONE':
            raise PermissionDenied('INVALID_REQUESTING_STATUS')

        serializer = self.get_serializer(
            data=request.data,
            context={ 'requesting_history': requesting_history, }
        )

        if serializer.is_valid(raise_exception=True):
            serializer.save()

            return Response(RequestingHistorySerializer(requesting_history).data)


@extend_schema(
    summary='의뢰 리뷰 목록 가져오기',
    description='의뢰 리뷰 목록 작성 API (의뢰인)',
)
class RequestingReviewListingView(generics.ListAPIView):
    parser_classes = [ MultiPartParser, ]
    permission_classes = (AllowAny,)
    serializer_class = ReviewSerializer

    def get_queryset(self):
        return Review.objects \
            .filter(
                Q(images__isnull=False)& \
                Q(is_exposing_to_dealer=True)
            ) \
            .order_by('-created_at')
