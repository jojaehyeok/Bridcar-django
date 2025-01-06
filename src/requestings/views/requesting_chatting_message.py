from django.db.models import Q

from rest_framework import generics, mixins, status, serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.exceptions import ParseError, NotFound, AuthenticationFailed

from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer

from users.permissions import IsOnlyForAgent

from vehicles.models import Car

from requestings.models import RequestingHistory, RequestingChattingMessage
from requestings.serializers import RequestingChattingMessageSerializer, WriteRequestingChattingMessageSerializer
from requestings.permissions import IsParticipatedRequesting
from requestings.constants import REQUESTING_CHATTING_SENDING_TO

from notifications.models import Notification


@extend_schema(
    methods=[ 'GET', ],
    summary='의뢰 채팅 메시지 가져오기',
    description='의뢰 채팅 메시지 가져오기 API',
    parameters=[
        OpenApiParameter(
            name='receiving_from',
            location=OpenApiParameter.QUERY,
            description=f'해당 사람이 보낸 메시지만 가져오기 { ", ".join(dict(REQUESTING_CHATTING_SENDING_TO).keys()) }',
            required=True,
            type=int
        ),
        OpenApiParameter(
            name='message_id_after',
            location=OpenApiParameter.QUERY,
            description=f'해당 id 뒤로만 메시지 가져오기',
            required=False,
            type=int
        ),
    ],
    responses={
        200: RequestingChattingMessageSerializer,
    }
)
@extend_schema(
    methods=[ 'POST', ],
    summary='의뢰 채팅 메시지 작성',
    request=WriteRequestingChattingMessageSerializer,
    description='의뢰 채팅 메시지 작성 API',
)
class RequestingChattingView(mixins.ListModelMixin, generics.GenericAPIView):
    parser_classes = (MultiPartParser,)
    permission_classes = [ IsParticipatedRequesting, ]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RequestingChattingMessageSerializer
        elif self.request.method == 'POST':
            return WriteRequestingChattingMessageSerializer

    def get_object(self, pk):
        try:
            return RequestingHistory.objects.get(pk=pk)
        except RequestingHistory.DoesNotExist:
            raise NotFound('INVALID_REQUESTING')

    def get_queryset(self):
        requesting_id = self.kwargs.get('id')
        requesting_history = self.get_object(requesting_id)

        receiving_from = self.request.query_params.get('receiving_from')
        message_id_after = self.request.query_params.get('message_id_after', None)

        queryset = RequestingChattingMessage.objects \
            .filter(Q(requesting_history__pk=requesting_id)) \
            .order_by('-created_at')

        if receiving_from == 'client':
            queryset = queryset.filter(
                Q(user=self.request.user)| \
                Q(user=requesting_history.client)
            )
        elif receiving_from == 'agent':
            queryset = queryset.filter(
                (
                    Q(sending_to='agent')& \
                    Q(user=self.request.user)
                )| \
                Q(user=requesting_history.agent)
            )
        elif receiving_from == 'deliverer':
            queryset = queryset.filter(
                (
                    Q(sending_to='deliverer')& \
                    Q(user=self.request.user)
                )| \
                Q(user=requesting_history.deliverer)
            )

        try:
            if int(message_id_after) != None:
                queryset = queryset.filter(Q(id__gt=message_id_after))
        except:
            pass

        return queryset

    def get(self, request, *args, **kwargs):
        user = request.user
        requesting_history = self.get_object(kwargs.get('id'))

        unread_messages = requesting_history.chatting_messages.filter(~Q(read_users=user))

        for message in unread_messages:
            message.read_users.add(user)

        return super(RequestingChattingView, self).list(request, *args, **kwargs)

    def post(self, request, id):
        user = request.user
        requesting_history = self.get_object(id)

        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            sending_to = serializer.validated_data.get('sending_to', None)
            image = serializer.validated_data.get('image', None)

            chatting_message = serializer.save(
                user=user,
                requesting_history=requesting_history,
            )

            notification_body_message = '이미지를 보냈습니다.' if image != None else serializer.validated_data.get('text')

            if (user == requesting_history.agent or user == requesting_history.deliverer) and \
                    (sending_to == None or sending_to == 'client'):
                Notification.create(
                    'USER',
                    'REQUESTING_CHATTING',
                    user=requesting_history.client,
                    actor=user,
                    data=requesting_history,
                    requesting_history=requesting_history,
                    body_message=notification_body_message,
                )
            elif sending_to == 'agent':
                Notification.create(
                    'USER',
                    'REQUESTING_CHATTING',
                    user=requesting_history.agent,
                    actor=user,
                    data=requesting_history,
                    requesting_history=requesting_history,
                    body_message=notification_body_message,
                )
            elif sending_to == 'deliverer':
                Notification.create(
                    'USER',
                    'REQUESTING_CHATTING',
                    user=requesting_history.deliverer,
                    actor=user,
                    data=requesting_history,
                    requesting_history=requesting_history,
                    body_message=notification_body_message,
                )

            return Response(RequestingChattingMessageSerializer(chatting_message).data)
