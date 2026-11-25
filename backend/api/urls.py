from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    admin_profile, forgot_password, WorkerViewSet,
    mark_face_attendance, list_attendance, analyze_image,
    get_media_list, analyze_video_frame, ViolationViewSet,
    get_notifications, dashboard_stats, generate_report,
    ai_system_status, ai_system_config
)

router = DefaultRouter()
router.register(r'workers', WorkerViewSet, basename='worker')
router.register(r'violations', ViolationViewSet, basename='violation')

urlpatterns = [
    path('auth/profile/', admin_profile, name='admin_profile'),
    path('auth/forgot-password/', forgot_password, name='forgot_password'),
    
    path('system/status/', ai_system_status, name='ai_system_status'),
    path('system/settings/', ai_system_config, name='ai_system_config'),

    path('attendance/mark/', mark_face_attendance, name='mark_face_attendance'),
    path('attendance/', list_attendance, name='list_attendance'),
    
    path('analysis/image/', analyze_image, name='analyze_image'),
    path('analysis/media/', get_media_list, name='get_media_list'),
    path('analysis/video-frame/', analyze_video_frame, name='analyze_video_frame'),
    
    path('notifications/', get_notifications, name='get_notifications'),
    path('dashboard/stats/', dashboard_stats, name='dashboard_stats'),
    path('reports/', generate_report, name='generate_report'),

    path('', include(router.urls)),
]
