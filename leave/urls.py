from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import LeaveRequestViewSet

router = DefaultRouter()
router.register(r'leave-requests', LeaveRequestViewSet, basename='leaverequest')

urlpatterns = [
    path('', include(router.urls)),
]
