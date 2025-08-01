from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import DepartmentViewSet

router = DefaultRouter()
router.register(r'', DepartmentViewSet, basename='department')

urlpatterns = [
    path('', include(router.urls)),
]
