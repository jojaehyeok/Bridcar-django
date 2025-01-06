from django.urls import path, include

from fcm_django.api.rest_framework import FCMDeviceAuthorizedViewSet

from . import views

urlpatterns = [
    path('current', views.UserSelfDetailView.as_view()),
    path('signin', views.SigninView.as_view()),
    path('signout', views.SignoutView.as_view()),
    path('devices', FCMDeviceAuthorizedViewSet.as_view({'post': 'create'})),
    path('token/refresh', views.TokenRefreshView.as_view()),
    path('dealers/signup', views.DealerSignupView.as_view()),
    path('dealers/recent-addresses', views.DealerRecentlyUsingAddressListView.as_view()),
    path('balance-histories', views.BalanceHistoryListView.as_view()),
    path('balance-histories/deposits', views.RequestDepositView.as_view()),
    path('balance-histories/deposits/results', views.UpdateDepositResultView.as_view()),
    path('balance-histories/withdrawals', views.RequestWithdrawalView.as_view()),
    path('authentications/sms', views.RequestSMSAuthenticationView.as_view()),
    path('dealers/profiles/current', views.DealerProfileView.as_view()),
    path('dealers/profiles/current/files', views.DealerBusinessRegistrationView.as_view()),
    path('agents', views.AgentListView.as_view()),
    path('agents/profiles/current', views.UpdateAgentProfileView.as_view()),
    path('agents/settlement-account', views.UpdateAgentSettlementAccountView.as_view()),
    path('agents/locations/coord/current', views.AgentCurrentLocationView.as_view()),
    path('agents/locations/configs', views.ConfigLocationView.as_view()),
    path('agents/locations/working', views.AgentEndWorkingView.as_view()),
]
