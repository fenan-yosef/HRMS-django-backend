from rest_framework import viewsets, permissions, status
from .permissions import AnyOf, IsCEO, IsHR, IsManager
from rest_framework.response import Response
import traceback
from django.shortcuts import render
from django.middleware.csrf import get_token
from .models import CustomUser, Department, PerformanceReview, Attendance
from employee.models import Employee  # Import Employee model
from .serializers import UserSerializer, DepartmentSerializer, PerformanceReviewSerializer, AttendanceSerializer
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer
from django.contrib.auth import authenticate
from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)

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

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class MeView(APIView):
    """Endpoint to retrieve data for the current authenticated user."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            data = UserSerializer(user).data
            # If the user is an employee, fetch first_name and last_name from Employee model
            if user.role.lower() == 'employee':
                employee = None
                try:
                    if hasattr(user, 'employee_profile'):
                        employee = user.employee_profile
                    else:
                        from employee.models import Employee as EmployeeModel
                        employee = EmployeeModel.objects.filter(email=user.email).first()
                except Exception as e:
                    logger.warning(f"Could not fetch Employee profile for user {user.email}: {e}")
                if employee:
                    data['first_name'] = employee.first_name
                    data['last_name'] = employee.last_name
            return Response(data)
        except Exception as e:
            logger.error(f"Error retrieving user data: {e}", exc_info=True)
            return Response(
                {'errors': {'detail': 'Unable to retrieve user information.'}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def put(self, request):
        user = request.user
        data = request.data.copy()
        try:
            # Update CustomUser fields
            user_serializer = UserSerializer(user, data=data, partial=True)
            user_serializer.is_valid(raise_exception=True)
            user_serializer.save()

            # If employee, update Employee fields as well
            if user.role.lower() == 'employee':
                employee = getattr(user, 'employee_profile', None)
                if employee:
                    from employee.serializers import EmployeeSerializer
                    # Only update fields that exist on Employee
                    emp_data = {k: v for k, v in data.items() if k in EmployeeSerializer.Meta.fields or k == 'department'}
                    emp_serializer = EmployeeSerializer(employee, data=emp_data, partial=True, context={'request': request})
                    emp_serializer.is_valid(raise_exception=True)
                    emp_serializer.save()
            return Response({'message': 'Profile updated successfully.'})
        except Exception as e:
            logger.error(f"Error updating user profile: {e}", exc_info=True)
            return Response(
                {'errors': {'detail': 'Unable to update user information.'}},
                status=status.HTTP_400_BAD_REQUEST
            )

def login_view(request):
    try:
        identifier = request.data.get("identifier")
        password = request.data.get("password")
        user = authenticate(request, identifier=identifier, password=password)
        if user is not None:
            # ...existing code for successful login...
            pass
        else:
            return JsonResponse({"errors": {"detail": "Invalid username/email or password."}}, status=400)
    except Exception as e:
        logger.error(f"Error during login: {e}", exc_info=True)
        return JsonResponse({"errors": {"detail": "An unexpected error occurred."}}, status=500)
