from django.db.models import Q

from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_framework.parsers import MultiPartParser
from rest_framework import generics, mixins, viewsets

from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer

from django_filters.rest_framework import DjangoFilterBackend

from notifications.models import Notification
from notifications.serializers import NotificationSerializer

from users.permissions import IsOnlyControlRoomUser


@extend_schema(
    summary='알림 목록',
    description='알림 목록 API',
    responses={
        200: NotificationSerializer(many=True)
    }
)
class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects \
            .filter(user=self.request.user) \
            .order_by('-created_at')


@extend_schema(
    summary='상황실 타임라인 목록 (상황실 전용)',
    description='상황실 타임라인 목록 API (상황실 전용)',
    parameters=[
        OpenApiParameter(
            name='id_after',
            location=OpenApiParameter.QUERY,
            description=f'해당 ID 이후거만 알림을 가져옴',
            required=False,
            type=str
        ),
    ],
    responses={
        200: NotificationSerializer(many=True)
    }
)
class ControlRoomNotificationListView(generics.ListAPIView):
    permission_classes = [ IsOnlyControlRoomUser, ]
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    filter_backends = [ DjangoFilterBackend, ]
    filterset_fields = {
        'subject': [ 'in', 'exact', ],
    }

    def get_queryset(self):
        id_after = self.request.query_params.get('id_after', None)

        queryset = Notification.objects \
            .filter(Q(type__contains='CONTROL_ROOM')) \
            .exclude(Q(requesting_history__status='CANCELLED')) \
            .order_by('-created_at')

        if id_after != None:
            queryset = queryset.filter(id__gt=id_after)

        return queryset


    def get(self, request, *args, **kwargs):
        id_after = self.request.query_params.get('id_after', None)

        if id_after == None:
            return super(ControlRoomNotificationListView, self).get(request, *args, **kwargs)
        else:
            queryset = self.filter_queryset(self.get_queryset())[:20]

            return Response(NotificationSerializer(queryset, many=True).data)


@extend_schema(
    summary='상황실 알림 읽기처리 (상황실 전용)',
    description='상황실 알림 읽기처리 API (상황실 전용)',
)
class ReadControllRoomNotification(generics.GenericAPIView):
    permission_classes = [ IsOnlyControlRoomUser, ]

    def get_object(self, pk):
        notification = Notification.objects \
            .filter(
                Q(pk=pk)& \
                Q(type__contains='CONTROL_ROOM')
            ) \
            .first()

        if notification is None:
            raise NotFound('NOTIFICATION_NOT_FOUND')

        return notification

    def post(self, request, id):
        notification = self.get_object(id)

        notification.is_read = True
        notification.save()

        return Response(None)
