from django.urls import path, include

from .views import ListAgreementView, AgreementDetailView

urlpatterns = [
    path('agreements', ListAgreementView.as_view()),
    path('agreements/<str:type>', AgreementDetailView.as_view()),
]
