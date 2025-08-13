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
        if user.role in ['CEO', 'HR', 'Manager']:
            return PerformanceReview.objects.all()
        return PerformanceReview.objects.filter(employee=user)

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [AnyOf(IsCEO, IsHR, IsManager)]
        return [permissions.IsAuthenticated()]
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
            data = UserSerializer(user).data
            dashboard = {}
            # Employee dashboard metrics
            if user.role.lower() == 'employee':
                from leave.models import LeaveRequest
                from hr.models import PerformanceReview, CustomUser
                # My Leave Days Used
                approved_leaves = LeaveRequest.objects.filter(employee=user, status='APPROVED')
                total_days = sum((leave.end_date - leave.start_date).days + 1 for leave in approved_leaves)
                dashboard['my_leave_days_used'] = total_days
                # My Pending Requests
                pending_requests = LeaveRequest.objects.filter(employee=user, status='PENDING').count()
                dashboard['my_pending_requests'] = pending_requests
                # Days Until Next Review
                next_review = PerformanceReview.objects.filter(employee=user, created_at__gt=timezone.now()).order_by('created_at').first()
                if next_review:
                    days_until_review = (next_review.created_at.date() - timezone.now().date()).days
                else:
                    days_until_review = None
                dashboard['days_until_next_review'] = days_until_review
                # My Team Size (employees in same department)
                team_size = CustomUser.objects.filter(department=user.department, role='employee').count() if user.department else 0
                dashboard['my_team_size'] = team_size
            # Manager dashboard metrics
            if user.role.lower() == 'manager':
                from hr.models import CustomUser, PerformanceReview, Attendance
                from leave.models import LeaveRequest
                from django.db.models import Avg
                today = timezone.now().date()
                # Team size: count employees in manager's department
                team_size = CustomUser.objects.filter(
                    department=user.department,
                    role__iexact='employee'
                ).count() if user.department else 0
                dashboard['my_team_size'] = team_size
                # Employees on leave today
                on_leave = Attendance.objects.filter(
                    employee__department=user.department,
                    status='Leave', date=today
                ).count() if user.department else 0
                dashboard['employees_on_leave'] = on_leave
                # Pending leave requests for team
                pending = LeaveRequest.objects.filter(
                    employee__department=user.department,
                    status='PENDING'
                ).count() if user.department else 0
                dashboard['pending_leave_requests'] = pending
                # New hires this month
                first_of_month = today.replace(day=1)
                new_hires = CustomUser.objects.filter(
                    department=user.department,
                    date_joined__gte=first_of_month
                ).count() if user.department else 0
                dashboard['new_hires_this_month'] = new_hires
                # Team performance metrics
                # Average performance score
                avg_score = PerformanceReview.objects.filter(
                    employee__department=user.department
                ).aggregate(avg=Avg('score'))['avg'] or 0
                dashboard['team_avg_performance_score'] = round(avg_score, 2)
                # Reviews this month
                reviews_month = PerformanceReview.objects.filter(
                    employee__department=user.department,
                    created_at__gte=first_of_month
                ).count() if user.department else 0
                dashboard['performance_reviews_this_month'] = reviews_month
            # CEO dashboard metrics
            if user.role.lower() == 'ceo':
                from hr.models import CustomUser, PerformanceReview, Attendance
                from leave.models import LeaveRequest
                from django.db.models import Count, Avg, Max
                from datetime import timedelta
                today = timezone.now().date()
                now = timezone.now()
                first_of_month = today.replace(day=1)
                last_30 = now - timedelta(days=30)
                # Headcount metrics
                total_users = CustomUser.objects.filter(deleted_at__isnull=True).count()
                employees = CustomUser.objects.filter(role__iexact='employee').count()
                managers = CustomUser.objects.filter(role__iexact='manager').count()
                hr_count = CustomUser.objects.filter(role__iexact='hr').count()
                dashboard['headcount'] = {
                    'total_active_users': total_users,
                    'employees': employees,
                    'managers': managers,
                    'hr': hr_count,
                }
                # Department distribution
                dept_counts = []
                for dept in Department.objects.all():
                    emp_count = CustomUser.objects.filter(department=dept, deleted_at__isnull=True).count()
                    dept_counts.append({'id': dept.id, 'name': dept.name, 'emp_count': emp_count})
                dashboard['departments'] = dept_counts
                # Hires this month (approx using date_joined)
                hires_this_month = CustomUser.objects.filter(date_joined__date__gte=first_of_month).count()
                dashboard['hires_this_month'] = hires_this_month
                # Soft-deleted (attrition) last 30 days
                deleted_last_30 = CustomUser.all_objects.filter(deleted_at__gte=last_30).count()
                previous_period_baseline = total_users + deleted_last_30 if (total_users + deleted_last_30) else 1
                attrition_rate = deleted_last_30 / previous_period_baseline
                dashboard['attrition_last_30_days'] = {
                    'count': deleted_last_30,
                    'rate': round(attrition_rate, 4)
                }
                # Leave metrics
                pending_leave = LeaveRequest.objects.filter(status='PENDING').count()
                approved_leave_today = LeaveRequest.objects.filter(status='APPROVED', start_date__lte=today, end_date__gte=today).count()
                dashboard['leave'] = {
                    'pending_requests': pending_leave,
                    'employees_on_approved_leave_today': approved_leave_today,
                }
                # Attendance today
                attendance_today = Attendance.objects.filter(date=today)
                dashboard['attendance_today'] = {
                    'present': attendance_today.filter(status='Present').count(),
                    'absent': attendance_today.filter(status='Absent').count(),
                    'leave': attendance_today.filter(status='Leave').count(),
                }
                # Performance metrics
                perf_qs = PerformanceReview.objects.all()
                avg_score = perf_qs.aggregate(avg=Avg('score'))['avg'] or 0
                reviews_this_month = perf_qs.filter(created_at__date__gte=first_of_month).count()
                # Top performers (latest score per employee, naive: take max score)
                top_performers = (
                    perf_qs.values('employee__id', 'employee__first_name', 'employee__last_name')
                    .annotate(max_score=Max('score'))
                    .order_by('-max_score')[:5]
                )
                dashboard['performance'] = {
                    'average_score': round(avg_score, 2),
                    'reviews_this_month': reviews_this_month,
                    'top_performers': list(top_performers),
                }
                # Age distribution buckets (if date_of_birth exists)
                ages = []
                for dob in CustomUser.objects.filter(date_of_birth__isnull=False).values_list('date_of_birth', flat=True):
                    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                    ages.append(age)
                buckets = {'<25':0,'25-34':0,'35-44':0,'45-54':0,'55+':0}
                for a in ages:
                    if a < 25: buckets['<25'] += 1
                    elif a < 35: buckets['25-34'] += 1
                    elif a < 45: buckets['35-44'] += 1
                    elif a < 55: buckets['45-54'] += 1
                    else: buckets['55+'] += 1
                dashboard['age_distribution'] = buckets
            data['dashboard'] = dashboard
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
