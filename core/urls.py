from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SystemSettingViewSet

router = DefaultRouter()
router.register(r'system', SystemSettingViewSet, basename='system-setting')

urlpatterns = [
    path('', include(router.urls)),
]
