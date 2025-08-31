from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SystemSettingViewSet, SystemSettingByKeyView, AuditLogViewSet

router = DefaultRouter()
router.register(r'system', SystemSettingViewSet, basename='system-setting')
router.register(r'logs', AuditLogViewSet, basename='audit-log')

urlpatterns = [
    path('', include(router.urls)),
    path('system/by-key/<str:key>/', SystemSettingByKeyView.as_view(), name='system-setting-by-key'),
]
