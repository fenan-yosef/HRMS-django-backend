from rest_framework import viewsets, permissions
from .models import CustomUser, Department
from .serializers import UserSerializer, DepartmentSerializer
from .permissions import IsCEO, IsHR

class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'DELETE']:
            return [IsCEO() | IsHR()]
        return [permissions.IsAuthenticated()]

class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer

    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'DELETE']:
            return [IsCEO() | IsHR()]
        return [permissions.IsAuthenticated()]
