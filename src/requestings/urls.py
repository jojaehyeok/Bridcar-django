from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.RequestingHistoryView.as_view()),
    path('bulks', views.UploadBulkRequestingView.as_view()),
    path('costs', views.LookupRequestingCostView.as_view()),
    path('reviews', views.RequestingReviewListingView.as_view()),
    path('waiting-allocations', views.WaitingAllocationsRequestingHistoryView.as_view()),
    path('waiting-allocations/<int:id>', views.WaitingAllocationsRequestingHistoryDetailView.as_view()),
    path('workings', views.WorkingRequestingHistoryView.as_view()),
    path('finishes', views.FinishesRequestingHistoryView.as_view()),
    path('settlements', views.RequestingSettlementView.as_view()),
    path('settlements/monthly', views.MonthlyRequestingSettlementView.as_view()),
    path('<int:id>/reviews', views.WriteRequestingReviewView.as_view()),
    path('external-evaluation-templates', views.ListExternalEvaluationTemplatesView.as_view()),
    path('<int:id>', views.RequestingHistoryDetailView.as_view()),
    path('<int:id>/chatting-messages', views.RequestingChattingView.as_view()),
    path('<int:id>/applyings', views.ApplyRequestingView.as_view()),
    path('<int:id>/pre-informations', views.RequestingPreInformationView.as_view()),
    #path('<int:id>/evaluations/costs', views.RequestingCostView.as_view()),
    path('<int:id>/evaluations/starting', views.StartRequestingEvaluationView.as_view()),
    path('<int:id>/evaluations/finishing', views.FinishRequestingEvaluationView.as_view()),
    path('<int:id>/evaluations/confirmation', views.ConfirmRequestingEvaluationView.as_view()),
    path('<int:id>/inspections/confirmation', views.ConfirmInspectionResultView.as_view()),
    path('<int:id>/delivery/handover', views.HandoverDeliveryView.as_view()),
    path('<int:id>/delivery/departure', views.RequestingDeliveryDepartView.as_view()),
    path('<int:id>/delivery/arrival', views.RequestingDeliveryArriveView.as_view()),
    path('<int:id>/delivery/receiving', views.RequestingDeliveryReceivingView.as_view()),
]
