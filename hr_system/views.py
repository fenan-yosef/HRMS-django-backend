# hr_system/views.py

from rest_framework import viewsets, permissions
from .models import Employee, Department, Leave, PerformanceReview
from .serializers import (
    EmployeeListSerializer, 
    EmployeeDetailSerializer, 
    DepartmentSerializer, 
    LeaveSerializer, 
    PerformanceReviewSerializer
)
# Import the custom permissions we just created
from .permissions import IsAdminOrReadOnly, IsEmployeeOwner, IsManagerAndOwnerOrReadOnly

class DepartmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows departments to be viewed or edited.
    Only Admins (staff users) can create, update, or delete departments.
    """
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    # Apply the permission: Read-only for everyone, write for Admins.
    permission_classes = [IsAdminOrReadOnly]

class EmployeeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows employees to be viewed or edited.
    - Anyone can list employees (for a company directory).
    - Only the employee themselves can edit their profile.
    - Admins have full access.
    """
    queryset = Employee.objects.select_related('department', 'manager').all()
    # Apply the permission: Anyone can view, only owner can edit.
    permission_classes = [permissions.IsAuthenticated, IsEmployeeOwner]
    
    def get_serializer_class(self):
        """
        Determines which serializer to use based on the action.
        """
        if self.action == 'list':
            return EmployeeListSerializer
        return EmployeeDetailSerializer

class LeaveViewSet(viewsets.ModelViewSet):
    """
    API endpoint for viewing and creating leave requests.
    - Employees can only manage their own leave requests.
    - Managers can view their team's requests.
    - Admins can see all requests.
    """
    serializer_class = LeaveSerializer
    # Apply permission: Must be authenticated, and must be owner or manager.
    permission_classes = [permissions.IsAuthenticated, IsManagerAndOwnerOrReadOnly]

    def get_queryset(self):
        """
        This view should return a list of all the leave requests
        for the currently authenticated user's team or themselves.
        Admins should see all leave requests.
        """
        user = self.request.user
        if user.is_staff:
            return Leave.objects.all()
        # Return requests for the user and their direct reports
        return Leave.objects.filter(employee__in=Employee.objects.filter(manager=user.employee) | Employee.objects.filter(pk=user.employee.pk))
        
    def perform_create(self, serializer):
        """
        Automatically set the employee for a new leave request to the current user.
        """
        serializer.save(employee=self.request.user.employee)


class PerformanceReviewViewSet(viewsets.ModelViewSet):
    """
    API endpoint for performance reviews.
    Permissions follow the same logic as Leave requests.
    """
    serializer_class = PerformanceReviewSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerAndOwnerOrReadOnly]

    def get_queryset(self):
        """
        Admins see all reviews.
        Managers see reviews for their reports.
        Employees see their own reviews.
        """
        user = self.request.user
        if user.is_staff:
            return PerformanceReview.objects.all()
        return PerformanceReview.objects.filter(employee__in=Employee.objects.filter(manager=user.employee) | Employee.objects.filter(pk=user.employee.pk))
