from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.NotificationListView.as_view()),
    path('activities', views.ControlRoomNotificationListView.as_view()),
    path('activities/<str:id>', views.ReadControllRoomNotification.as_view()),
]
