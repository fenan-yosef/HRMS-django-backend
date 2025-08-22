from rest_framework import viewsets, permissions, status
from django.utils import timezone
from django.db import models
from .permissions import AnyOf, IsCEO, IsHR, IsManager, IsManagerOfDepartment
from rest_framework.response import Response
import traceback
from django.shortcuts import render
from django.middleware.csrf import get_token
from .models import CustomUser, PerformanceReview, Attendance
from department.models import Department
from .serializers import UserSerializer, DepartmentSerializer, PerformanceReviewSerializer, AttendanceSerializer
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer
from django.contrib.auth import authenticate
from django.http import JsonResponse
import logging
from rest_framework.decorators import api_view, action
from .serializers import HighLevelUserSerializer

logger = logging.getLogger(__name__)

class UserViewSet(viewsets.ModelViewSet):
    @action(detail=True, methods=['post'], url_path='demote', url_name='demote')
    def demote_to_employee(self, request, pk=None):
        user = self.get_object()
        requester = request.user
        # Only CEO or HR can demote
        if str(getattr(requester, 'role', '')).lower() not in ['ceo', 'hr']:
            return Response({'error': 'Only CEO or HR can demote managers.'}, status=403)
        if str(user.role).lower() != 'manager':
            return Response({'detail': 'User is not a manager.'}, status=400)
        user.role = 'employee'
        user.save(update_fields=['role'])
        return Response({'detail': f'{user.email} demoted to employee.'})
    from rest_framework.decorators import action

    @action(detail=True, methods=['post'], url_path='promote', url_name='promote')
    def promote_to_manager(self, request, pk=None):
        user = self.get_object()
        requester = request.user
        # Only CEO or HR can promote
        if str(getattr(requester, 'role', '')).lower() not in ['ceo', 'hr']:
            return Response({'error': 'Only CEO or HR can promote employees.'}, status=403)
        if str(user.role).lower() == 'manager':
            return Response({'detail': 'User is already a manager.'}, status=400)
        user.role = 'manager'
        user.save(update_fields=['role'])
        return Response({'detail': f'{user.email} promoted to manager.'})
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer

    def get_queryset(self):
        """
        Filter users by role query param first, then restrict to manager's department if requester is a manager.
        """
        queryset = CustomUser.objects.all()
        # Apply role filter if provided
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(role__iexact=role)
        # Apply department filter if provided
        dept = self.request.query_params.get('department')
        if dept:
            try:
                dept_id = int(dept)
                queryset = queryset.filter(department_id=dept_id)
            except (ValueError, TypeError):
                # ignore invalid department param and leave queryset unchanged
                pass
        # Managers only see users in their own department
        user = self.request.user
        if getattr(user, 'role', '').lower() == 'manager':
            queryset = queryset.filter(department=user.department)
        return queryset

    def get_permissions(self):
        user = self.request.user
        # Allow managers to create employees
        if self.request.method == 'POST':
            return [AnyOf(IsCEO, IsHR, IsManager)]
        # Update/delete: managers restricted to own department
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            if user.is_authenticated and user.role and user.role.lower() == 'manager':
                return [IsManagerOfDepartment()]
            return [AnyOf(IsCEO, IsHR)]
        # Retrieve detail: managers restricted to own department
        if self.request.method == 'GET' and self.action == 'retrieve' and user.is_authenticated and user.role and user.role.lower() == 'manager':
            return [permissions.IsAuthenticated(), IsManagerOfDepartment()]
        # List and other GET: any authenticated can list,
        # but get_queryset already filters managers
        return [permissions.IsAuthenticated()]

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = request.data.copy()
        # Managers cannot change department; enforce their own
        if request.user.role and request.user.role.lower() == 'manager':
            data.pop('department_id', None)
        password_changed = 'password' in data
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        response_data = serializer.data
        if password_changed:
            response_data['message'] = 'Password changed successfully.'
        return Response(response_data)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        # Managers automatically set department
        user = self.request.user
        if user.role and user.role.lower() == 'manager':
            serializer.save(department=user.department)
        else:
            serializer.save()

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
        role = str(getattr(user, 'role', '')).lower()
        if role in ['ceo', 'hr', 'manager']:
            return PerformanceReview.objects.all().select_related('employee', 'reviewer', 'review_cycle').prefetch_related('scores__competency')
        return PerformanceReview.objects.filter(employee=user).select_related('employee', 'reviewer', 'review_cycle').prefetch_related('scores__competency')

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [AnyOf(IsCEO, IsHR, IsManager)]
        return [permissions.IsAuthenticated()]

class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all().select_related('employee')
    serializer_class = AttendanceSerializer

    def get_queryset(self):
        user = self.request.user
        role = getattr(user, 'role', '').lower()
        qs = Attendance.objects.all().select_related('employee')
        if role in ['ceo', 'hr']:
            return qs
        if role == 'manager':
            # Manager sees own + team (same department, employees only)
            if user.department_id:
                return qs.filter(models.Q(employee=user) | models.Q(employee__department_id=user.department_id))
            return qs.filter(employee=user)
        # Employee only self
        return qs.filter(employee=user)

    def get_permissions(self):
        if self.action in ['destroy', 'update', 'partial_update', 'create']:
            # Direct CRUD only for HR/CEO (normal users use custom actions)
            return [AnyOf(IsCEO, IsHR)]
        return [permissions.IsAuthenticated()]

    @action(detail=False, methods=['post'], url_path='check-in')
    def check_in(self, request):
        user = request.user
        today = timezone.localdate()
        att, created = Attendance.objects.get_or_create(employee=user, date=today, defaults={'status': 'Present'})
        if att.check_in_time:
            return Response({'detail': 'Already checked in.', 'check_in_time': att.check_in_time}, status=400)
        att.check_in_time = timezone.localtime().time()
        att.status = 'Present'
        att.save(update_fields=['check_in_time', 'status'])
        return Response({'detail': 'Check-in recorded', 'time': att.check_in_time})

    @action(detail=False, methods=['post'], url_path='check-out')
    def check_out(self, request):
        user = request.user
        today = timezone.localdate()
        try:
            att = Attendance.objects.get(employee=user, date=today)
        except Attendance.DoesNotExist:
            return Response({'detail': 'No check-in found for today.'}, status=400)
        if not att.check_in_time:
            return Response({'detail': 'Cannot check-out without check-in.'}, status=400)
        if att.check_out_time:
            total_hours = None
            if att.work_duration:
                total_hours = round(att.work_duration.total_seconds() / 3600, 2)
            return Response({'detail': 'Already checked out.', 'check_out_time': att.check_out_time, 'total_hours': total_hours}, status=400)
        att.check_out_time = timezone.localtime().time()
        att.save(update_fields=['check_out_time'])
        att.finalize_duration()
        total_hours = None
        if att.work_duration:
            total_hours = round(att.work_duration.total_seconds() / 3600, 2)
        return Response({'detail': 'Check-out recorded', 'time': att.check_out_time, 'total_hours': total_hours})

    @action(detail=False, methods=['get'], url_path='today')
    def today(self, request):
        user = request.user
        today = timezone.localdate()
        att = Attendance.objects.filter(employee=user, date=today).first()
        data = AttendanceSerializer(att).data if att else None
        return Response({'today': data})

    @action(detail=False, methods=['get'], url_path='monthly-summary')
    def monthly_summary(self, request):
        user = request.user
        role = getattr(user, 'role', '').lower()
        month = int(request.query_params.get('month', timezone.localdate().month))
        year = int(request.query_params.get('year', timezone.localdate().year))
        start = timezone.datetime(year, month, 1, tzinfo=timezone.get_current_timezone())
        # Next month start for range end
        if month == 12:
            end = timezone.datetime(year + 1, 1, 1, tzinfo=timezone.get_current_timezone())
        else:
            end = timezone.datetime(year, month + 1, 1, tzinfo=timezone.get_current_timezone())
        qs = Attendance.objects.filter(date__gte=start.date(), date__lt=end.date())
        if role in ['ceo', 'hr']:
            pass
        elif role == 'manager':
            if user.department_id:
                qs = qs.filter(models.Q(employee=user) | models.Q(employee__department_id=user.department_id))
            else:
                qs = qs.filter(employee=user)
        else:
            qs = qs.filter(employee=user)
        total_days = qs.count()
        present = qs.filter(status='Present').count()
        leave = qs.filter(status='Leave').count()
        absent = qs.filter(status='Absent').count()
        total_hours = qs.aggregate(sum=models.Sum('work_duration'))['sum'] or timezone.timedelta(0)
        return Response({
            'month': month,
            'year': year,
            'records': AttendanceSerializer(qs, many=True).data,
            'stats': {
                'total_days_recorded': total_days,
                'present': present,
                'leave': leave,
                'absent': absent,
                'total_hours': round(total_hours.total_seconds() / 3600, 2) if total_hours else 0,
            }
        })

    @action(detail=False, methods=['post'], url_path='reset-today', permission_classes=[AnyOf(IsCEO, IsHR)])
    def reset_today(self, request):
        """Admin ability to clear today attendance for a user (for corrections)."""
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'detail': 'user_id required'}, status=400)
        today = timezone.localdate()
        att = Attendance.objects.filter(employee_id=user_id, date=today).first()
        if not att:
            return Response({'detail': 'No record to reset'}, status=404)
        att.check_in_time = None
        att.check_out_time = None
        att.work_duration = None
        att.status = 'Absent'
        att.save(update_fields=['check_in_time', 'check_out_time', 'work_duration', 'status'])
        return Response({'detail': 'Attendance reset to Absent.'})

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class MeView(APIView):
    def patch(self, request):
        user = request.user
        data = request.data.copy()
        try:
            user_serializer = UserSerializer(user, data=data, partial=True)
            user_serializer.is_valid(raise_exception=True)
            user_serializer.save()
            return Response({'message': 'Profile updated successfully.'})
        except Exception as e:
            logger.error(f"Error updating user profile (PATCH): {e}", exc_info=True)
            return Response(
                {'errors': {'detail': 'Unable to update user information.'}},
                status=status.HTTP_400_BAD_REQUEST
            )
    """Endpoint to retrieve data for the current authenticated user."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            from .services.dashboard import build_dashboard
            data = UserSerializer(user).data
            data['dashboard'] = build_dashboard(user)
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

@api_view(['GET'])
def get_high_level_users(request):
    roles = ['hr', 'manager', 'ceo']
    users = CustomUser.objects.filter(role__in=roles)
    serializer = HighLevelUserSerializer(users, many=True)
    return Response(serializer.data)
