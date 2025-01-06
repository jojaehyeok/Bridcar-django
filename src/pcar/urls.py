"""pcar URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from users import urls as users_urls
from vehicles import urls as vehicel_urls
from requestings import urls as requesting_urls
from notifications import urls as notification_urls
from boards import urls as board_urls
from daangn import urls as daangn_urls

urlpatterns = [
    path('admin/dynamic_raw_id/', include('dynamic_raw_id.urls')),
    path('admin/', admin.site.urls),
    path('_nested_admin/', include('nested_admin.urls')),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('v1/users/', include(users_urls)),
    path('v1/vehicles/', include(vehicel_urls)),
    path('v1/requestings/', include(requesting_urls)),
    path('v1/notifications/', include(notification_urls)),
    path('v1/boards/', include(board_urls)),
    path('v1/daangn/', include(daangn_urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL.replace(settings.PUBLIC_URL, ''), document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    urlpatterns += [
        path('schema/', SpectacularAPIView.as_view(), name='schema'),
        path('daangn-schema/', SpectacularAPIView.as_view(urlconf='daangn.urls'), name='daangn-schema'),
        path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
        path('daangn-swagger/', SpectacularSwaggerView.as_view(url_name='daangn-schema'), name='swagger-ui'),
    ]
