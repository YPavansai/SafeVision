import os
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views.static import serve
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


def health_check(request):
    """Lightweight healthcheck endpoint for Render."""
    return JsonResponse({'status': 'ok', 'service': 'SafeVision API'})


def root_handler(request, path=''):
    frontend_url = os.environ.get('FRONTEND_URL')
    if frontend_url:
        return redirect(f"{frontend_url.rstrip('/')}/{path}")
    if settings.DEBUG:
        return redirect(f"http://localhost:3000/{path}")
    return JsonResponse({'status': 'ok', 'service': 'SafeVision API'})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health_check, name='health_check'),
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/', include('api.urls')),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    re_path(r'^(?P<path>.*)$', root_handler),
]
