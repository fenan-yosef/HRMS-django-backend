from rest_framework import viewsets, permissions, status
from django.utils import timezone
from django.db import models
from django.db.models import Count, Avg, Q
from django.db.models.functions import TruncMonth, TruncWeek
from .permissions import AnyOf, IsCEO, IsHR, IsManager, IsManagerOfDepartment
from rest_framework.response import Response
import traceback
from django.shortcuts import render
from django.middleware.csrf import get_token
from .models import CustomUser, PerformanceReview, Attendance, Complaint
from department.models import Department
from .serializers import UserSerializer, DepartmentSerializer, PerformanceReviewSerializer, AttendanceSerializer, ComplaintSerializer
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer
from django.contrib.auth import authenticate
from django.http import JsonResponse
import logging
from rest_framework.decorators import api_view, action
from .serializers import HighLevelUserSerializer
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta

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


class ComplaintViewSet(viewsets.ModelViewSet):
    queryset = Complaint.objects.all().select_related('created_by', 'target_user')
    serializer_class = ComplaintSerializer

    def get_queryset(self):
        user = self.request.user
        role = str(getattr(user, 'role', '')).lower()
        qs = Complaint.objects.all().select_related('created_by', 'target_user')
        if role in ['ceo', 'hr']:
            return qs
        if role == 'manager':
            # Manager sees complaints they created and those about users in their department
            dept_id = getattr(user, 'department_id', None)
            return qs.filter(models.Q(created_by=user) | models.Q(target_user__department_id=dept_id))
        # Employee: see only their created complaints
        return qs.filter(created_by=user)

    def get_permissions(self):
        if self.action in ['create']:
            # Any authenticated user can create (Employee, Manager, HR, CEO)
            return [permissions.IsAuthenticated()]
        if self.action in ['update', 'partial_update', 'destroy']:
            # Only HR/CEO can modify status or delete
            return [AnyOf(IsCEO, IsHR)]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        complaint = serializer.save(created_by=self.request.user)
        self._send_complaint_email(complaint)

    @action(detail=True, methods=['post'], url_path='set-status', permission_classes=[AnyOf(IsCEO, IsHR)])
    def set_status(self, request, pk=None):
        complaint = self.get_object()
        status_val = request.data.get('status')
        if status_val not in dict(Complaint.STATUS_CHOICES):
            return Response({'detail': 'Invalid status.'}, status=400)
        complaint.status = status_val
        complaint.save(update_fields=['status'])
        return Response({'detail': 'Status updated.'})

    def _send_complaint_email(self, complaint: Complaint):
        try:
            subject = f"[{complaint.get_type_display()}] {complaint.subject}"
            body_lines = [
                f"From: {complaint.created_by.get_full_name() or complaint.created_by.email}",
                f"Type: {complaint.get_type_display()}",
                f"About: {complaint.target_user.get_full_name() or complaint.target_user.email if complaint.target_user else 'N/A'}",
                "",
                complaint.description,
            ]
            message = "\n".join(body_lines)

            # Recipients: all HR users, and CEO if send_to_ceo True
            hr_emails = list(CustomUser.objects.filter(role__iexact='hr', is_active=True).values_list('email', flat=True))
            to_emails = hr_emails
            if complaint.send_to_ceo:
                ceo_emails = list(CustomUser.objects.filter(role__iexact='ceo', is_active=True).values_list('email', flat=True))
                to_emails = list(set(hr_emails + ceo_emails))
            if not to_emails:
                return
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                to_emails,
                fail_silently=True,
            )
        except Exception:
            logger.exception("Failed to send complaint notification email")


class AnalyticsViewSet(viewsets.ViewSet):
    """Analytics endpoints for HR/CEO dashboards."""

    def get_permissions(self):
        # Restrict analytics to HR and CEO
        return [AnyOf(IsCEO, IsHR)]

    @action(detail=False, methods=['get'], url_path='headcount-by-department')
    def headcount_by_department(self, request):
        # Active users by department
        depts = (
            Department.objects
            .annotate(emp_count=Count('custom_users', filter=Q(custom_users__deleted_at__isnull=True)))
            .values('id', 'name', 'emp_count')
            .order_by('name')
        )
        return Response({'results': list(depts)})

    @action(detail=False, methods=['get'], url_path='hires-vs-exits')
    def hires_vs_exits(self, request):
        # Last N months (default 6)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        months = int(request.query_params.get('months', 6))
        today = timezone.localdate()
        # Build month start list, oldest first
        month_starts = []
        y, m = today.year, today.month
        for i in range(months - 1, -1, -1):
            mm = m - i
            yy = y
            while mm <= 0:
                mm += 12
                yy -= 1
            month_starts.append(timezone.datetime(yy, mm, 1, tzinfo=timezone.get_current_timezone()))
        labels = [dt.strftime('%Y-%m') for dt in month_starts]
        # Next month for range ends
        def next_month(dt):
            if dt.month == 12:
                return dt.replace(year=dt.year+1, month=1, day=1)
            return dt.replace(month=dt.month+1, day=1)
        hires = []
        exits = []
        for start in month_starts:
            end = next_month(start)
            h = User.objects.filter(date_joined__gte=start, date_joined__lt=end).count()
            # use all_objects to include soft-deleted users
            x = User.all_objects.filter(deleted_at__gte=start, deleted_at__lt=end).count()
            hires.append(h)
            exits.append(x)
        return Response({'labels': labels, 'hires': hires, 'exits': exits})

    @action(detail=False, methods=['get'], url_path='leave-status')
    def leave_status(self, request):
        # Last X days grouped by week (default 90 days)
        from leave.models import LeaveRequest
        days = int(request.query_params.get('days', 90))
        now = timezone.now()
        start = now - timedelta(days=days)
        qs = (LeaveRequest.objects
              .filter(applied_date__gte=start)
              .annotate(week=TruncWeek('applied_date'))
              .values('week', 'status')
              .annotate(count=Count('id'))
              .order_by('week'))
        # Build buckets
        buckets = {}
        for row in qs:
            week = row['week'].date().isoformat() if row['week'] else 'unknown'
            status_key = row['status']
            buckets.setdefault(week, {'PENDING': 0, 'APPROVED': 0, 'DENIED': 0})
            buckets[week][status_key] = row['count']
        labels = sorted(buckets.keys())
        pending = [buckets[w]['PENDING'] for w in labels]
        approved = [buckets[w]['APPROVED'] for w in labels]
        denied = [buckets[w]['DENIED'] for w in labels]
        return Response({'labels': labels, 'pending': pending, 'approved': approved, 'denied': denied})

    @action(detail=False, methods=['get'], url_path='tasks-pipeline')
    def tasks_pipeline(self, request):
        from tasks.models import Task
        dept_id = request.query_params.get('department_id')
        qs = Task.objects.all()
        if dept_id:
            qs = qs.filter(department_id=dept_id)
        by_status = qs.values('status').annotate(count=Count('id'))
        status_counts = {row['status']: row['count'] for row in by_status}
        now = timezone.now()
        overdue = qs.filter(due_date__lt=now).exclude(status__in=['done', 'archived']).count()
        return Response({'by_status': status_counts, 'overdue': overdue})

    @action(detail=False, methods=['get'], url_path='performance-avg-by-department')
    def performance_avg_by_department(self, request):
        rows = (
            PerformanceReview.objects
            .values('employee__department__id', 'employee__department__name')
            .annotate(avg_score=Avg('overall_score'), reviews=Count('id'))
            .order_by('employee__department__name')
        )
        results = []
        for r in rows:
            name = r['employee__department__name'] or 'Unassigned'
            results.append({'department_id': r['employee__department__id'], 'department': name, 'avg_score': round(r['avg_score'] or 0, 2), 'reviews': r['reviews']})
        return Response({'results': results})

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
