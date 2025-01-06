from django.urls import path, include

from . import views

urlpatterns = [
    path('cars/<int:id>/evaluations', views.SaveCarEvaluationResultView.as_view()),
    path('cars/<int:id>/evaluation-sheets', views.EvaluationSheetViewSet.as_view({'post': 'create'})),
    path('cars/<int:id>/performance-check-records', views.PerformanceCheckRecordsView.as_view()),
    path('cars/<int:id>/carhistory', views.StartCarhistoryCrawlingView.as_view()),
]
