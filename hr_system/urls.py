# hr_system/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DepartmentViewSet, 
    EmployeeViewSet, 
    LeaveViewSet, 
    PerformanceReviewViewSet
)

# A router in DRF automatically generates the URL patterns for a ViewSet.
# It's similar to how decorators can define routes in NestJS controllers.
router = DefaultRouter()
router.register(r'departments', DepartmentViewSet, basename='department')
router.register(r'employees', EmployeeViewSet, basename='employee')
router.register(r'leaves', LeaveViewSet, basename='leave')
router.register(r'reviews', PerformanceReviewViewSet, basename='performancereview')

# The API URLs are now determined automatically by the router.
# For example:
# /api/employees/ -> LIST (GET), CREATE (POST)
# /api/employees/{id}/ -> RETRIEVE (GET), UPDATE (PUT/PATCH), DELETE (DELETE)
urlpatterns = [
    path('', include(router.urls)),
]
