from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .permissions import IsCEOOrReadOnly
from .models import Department
from .serializers import DepartmentSerializer


class DepartmentViewSet(viewsets.ModelViewSet):
    """API endpoint for CRUD operations on Departments."""
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated, IsCEOOrReadOnly]
