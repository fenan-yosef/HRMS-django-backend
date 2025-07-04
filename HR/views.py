from rest_framework import viewsets, permissions
from .models import CustomUser, Department, LeaveRequest, PerformanceReview, Attendance
from .serializers import UserSerializer, DepartmentSerializer, LeaveRequestSerializer, PerformanceReviewSerializer, AttendanceSerializer
from .permissions import IsCEO, IsHR, IsManager, IsOwner, AnyOf
from django.shortcuts import render
from django.middleware.csrf import get_token

class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'DELETE']:
            return [AnyOf(IsCEO, IsHR)]
        return [permissions.IsAuthenticated()]

class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer

    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'DELETE']:
            return [AnyOf(IsCEO, IsHR)]
        return [permissions.IsAuthenticated()]

def get_csrf_token_view(request):
    csrf_token = get_token(request)
    return render(request, 'get_csrf_token.html', {'csrf_token': csrf_token})

class LeaveRequestViewSet(viewsets.ModelViewSet):
    queryset = LeaveRequest.objects.all()
    serializer_class = LeaveRequestSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role in ['CEO', 'HR', 'Manager']:
            return LeaveRequest.objects.all()
        return LeaveRequest.objects.filter(employee=user)

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), AnyOf(IsOwner, IsCEO, IsHR, IsManager)]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(employee=self.request.user)

class PerformanceReviewViewSet(viewsets.ModelViewSet):
    queryset = PerformanceReview.objects.all()
    serializer_class = PerformanceReviewSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role in ['CEO', 'HR', 'Manager']:
            return PerformanceReview.objects.all()
        return PerformanceReview.objects.filter(employee=user)

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [AnyOf(IsCEO, IsHR, IsManager)]
        return [permissions.IsAuthenticated()]

class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role in ['CEO', 'HR']:
            return Attendance.objects.all()
        elif user.role == 'Manager':
            # Assuming a manager can see attendance for users in their department
            # This requires a link from user to department, which is not explicit.
            # For now, managers see their own, just like employees.
            # A more complex implementation would be needed for team visibility.
            return Attendance.objects.filter(employee=user)
        return Attendance.objects.filter(employee=user)

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [AnyOf(IsCEO, IsHR)]
        return [permissions.IsAuthenticated()]
