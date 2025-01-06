from django.urls import path, include

from .views import IssueTokenView, DaangnCreateRequestingView, DaangnRequestingDetailView, \
                    DaangnRequestingPaymentConfirmationView, DaangnCancelRequestingView

urlpatterns = [
    path('token', IssueTokenView.as_view()),
    path('requests', DaangnCreateRequestingView.as_view()),
    path('requests/<int:id>', DaangnRequestingDetailView.as_view()),
    path('requests/<int:id>/payments/confirmation', DaangnRequestingPaymentConfirmationView.as_view()),
    path('requests/<int:id>/cancellation', DaangnCancelRequestingView.as_view()),
]
