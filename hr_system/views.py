# hr_system/views.py

from rest_framework import viewsets
from .models import Employee, Department, Leave, PerformanceReview
from .serializers import (
    EmployeeListSerializer, 
    EmployeeDetailSerializer, 
    DepartmentSerializer, 
    LeaveSerializer, 
    PerformanceReviewSerializer
)

# A ViewSet in DRF is like a Controller in NestJS. It defines the logic
# for a set of related endpoints (e.g., list, create, retrieve, update, delete).
# ModelViewSet provides all of these actions by default.

class DepartmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows departments to be viewed or edited.
    """
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    # TODO: Add permissions later to restrict access.

class EmployeeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows employees to be viewed or edited.
    """
    queryset = Employee.objects.select_related('department', 'manager').all()
    # We need to use different serializers for the 'list' and 'retrieve' actions.
    
    def get_serializer_class(self):
        """
        Determines which serializer to use based on the action.
        - Use EmployeeListSerializer for the 'list' view.
        - Use EmployeeDetailSerializer for the 'retrieve' (detail) view.
        """
        if self.action == 'list':
            return EmployeeListSerializer
        return EmployeeDetailSerializer
    # TODO: Add permissions to ensure managers can only see their team, etc.


class LeaveViewSet(viewsets.ModelViewSet):
    """
    API endpoint for viewing and creating leave requests.
    """
    queryset = Leave.objects.all()
    serializer_class = LeaveSerializer
    # TODO: Add permissions so employees can only see/edit their own leave.


class PerformanceReviewViewSet(viewsets.ModelViewSet):
    """
    API endpoint for performance reviews.
    """
    queryset = PerformanceReview.objects.all()
    serializer_class = PerformanceReviewSerializer
    # TODO: Add permissions.

