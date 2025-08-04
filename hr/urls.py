from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, get_csrf_token_view, PerformanceReviewViewSet, get_high_level_users
from .auth_views import RegisterView, LoginView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import CustomTokenObtainPairView, MeView
from . import password_reset

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'performance-reviews', PerformanceReviewViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/register/', RegisterView.as_view(), name='auth_register'),
    path('auth/login/', LoginView.as_view(), name='auth_login'),
    path('auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('get-csrf-token/', get_csrf_token_view, name='get_csrf_token'),
    path('auth/me/', MeView.as_view(), name='auth_me'),
    path('auth/request-password-reset/', password_reset.RequestPasswordResetView.as_view(), name='request_password_reset'),
    path('auth/reset-password/', password_reset.ResetPasswordView.as_view(), name='reset_password'),
    path('high-level-users/', get_high_level_users, name='high_level_users'),
]
