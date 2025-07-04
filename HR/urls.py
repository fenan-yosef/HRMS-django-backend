from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, DepartmentViewSet
from .auth_views import SignupView, LoginView

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'departments', DepartmentViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/signup/', SignupView.as_view()),
    path('auth/login/', LoginView.as_view()),
]
