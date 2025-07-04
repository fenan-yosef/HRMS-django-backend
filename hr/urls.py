from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, DepartmentViewSet, get_csrf_token_view, LeaveRequestViewSet, PerformanceReviewViewSet, AttendanceViewSet
from .auth_views import RegisterView, LoginView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'departments', DepartmentViewSet)
router.register(r'leave-requests', LeaveRequestViewSet)
router.register(r'performance-reviews', PerformanceReviewViewSet)
router.register(r'attendances', AttendanceViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/register/', RegisterView.as_view(), name='auth_register'),
    # path('auth/login/', LoginView.as_view(), name='auth_login'),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('get-csrf-token/', get_csrf_token_view, name='get_csrf_token'),
]
