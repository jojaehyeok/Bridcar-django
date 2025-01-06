from rest_framework import serializers

from notifications.models import Notification

from users.serializers import UserForNotificationSerializer

from requestings.serializers import RequestingHistorySerializerForNotification


class NotificationSerializer(serializers.ModelSerializer):
    user = UserForNotificationSerializer()
    actor = UserForNotificationSerializer()
    requesting_history = RequestingHistorySerializerForNotification()

    class Meta:
        model = Notification
        fields = '__all__'


