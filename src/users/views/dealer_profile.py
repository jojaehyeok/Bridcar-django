import hashlib

from rest_framework import generics, mixins, status, serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.exceptions import ParseError, NotFound, AuthenticationFailed

from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer

from users.models import User
from users.permissions import IsOnlyForGuest, IsOnlyForDealer
from users.serializers import UserSerializer, CreateDealerProfileSerializer, \
                                CreateDealerBusinessRegistrationSerializer

from locations.serializers import CommonLocationSerializer

@extend_schema(
    methods=[ 'PATCH', ],
    summary='딜러 프로필 수정',
    description='딜러 프로필 수정 API',
    request=CreateDealerProfileSerializer,
    responses={
        200: UserSerializer,
    }
)
class DealerProfileView(generics.GenericAPIView):
    serializer_class = (CreateDealerProfileSerializer)
    permission_classes = (IsOnlyForDealer,)

    def patch(self, request):
        user = request.user

        serializer = self.get_serializer(
            user.dealer_profile,
            data=request.data,
            partial=True,
        )

        if serializer.is_valid(raise_exception=True):
            serializer.save()

            return Response(UserSerializer(user).data)


@extend_schema(
    summary='딜러 사업자등록증 사본 입력',
    description='딜러 사업자등록증 사본 입력 API',
    request=CreateDealerBusinessRegistrationSerializer,
    responses={
        200: UserSerializer,
    }
)
class DealerBusinessRegistrationView(generics.GenericAPIView):
    permission_classes = (IsOnlyForDealer,)
    serializer_class = (CreateDealerBusinessRegistrationSerializer)
    parser_classes = (MultiPartParser,)

    def post(self, request):
        user = request.user
        serializer = self.get_serializer(user.dealer_profile, data=request.data)

        if serializer.is_valid(raise_exception=True):
            serializer.save()

            return Response(UserSerializer(user).data)


@extend_schema(
    summary='최근 사용한 주소 목록 가져오기',
    description='최근 사용한 주소 목록 가져오기 (딜러)',
    responses={
        200: CommonLocationSerializer(many=True),
    }
)
class DealerRecentlyUsingAddressListView(generics.GenericAPIView):
    permission_classes = (IsOnlyForDealer,)
    serializer_class = CommonLocationSerializer
    pagination_class = None

    def get_queryset(self):
        user = self.request.user

        return user.requestings \
            .order_by('-created_at') \
            .all()[:10]

    def get(self, request, *args, **kwargs):
        addresses = []
        address_hashes = []

        recent_requesting_histories = self.get_queryset()

        for requesting_history in recent_requesting_histories:
            if requesting_history.source_location is not None:
                source_location_enc = hashlib.md5()
                source_location_enc.update(f'{ requesting_history.source_location.road_address }{ requesting_history.source_location.detail_address }'.encode())

                source_location_hash = source_location_enc.hexdigest()

                if source_location_hash not in address_hashes:
                    address_hashes.append(source_location_hash)
                    addresses.append(CommonLocationSerializer(requesting_history.source_location).data)

            if requesting_history.destination_location is not None:
                destination_location_enc = hashlib.md5()
                destination_location_enc.update(f'{ requesting_history.destination_location.road_address }{ requesting_history.destination_location.detail_address }'.encode())

                destination_location_hash = destination_location_enc.hexdigest()

                if destination_location_hash not in address_hashes:
                    address_hashes.append(destination_location_hash)
                    addresses.append(CommonLocationSerializer(requesting_history.destination_location).data)

        return Response(addresses)
