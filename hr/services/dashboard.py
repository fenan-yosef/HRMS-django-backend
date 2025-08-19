from django.utils import timezone
from django.db import models
from django.contrib.auth import get_user_model
from department.models import Department
from leave.models import LeaveRequest
from hr.models import PerformanceReview, Attendance


def employee_dashboard(user):
    data = {}
    approved_leaves = LeaveRequest.objects.filter(employee=user, status=LeaveRequest.Status.APPROVED)
    total_days = sum((l.end_date - l.start_date).days + 1 for l in approved_leaves)
    data['my_leave_days_used'] = total_days
    pending_requests = LeaveRequest.objects.filter(employee=user, status=LeaveRequest.Status.PENDING).count()
    data['my_pending_requests'] = pending_requests
    next_review = PerformanceReview.objects.filter(employee=user, created_at__gt=timezone.now()).order_by('created_at').first()
    data['days_until_next_review'] = (next_review.created_at.date() - timezone.now().date()).days if next_review else None
    User = get_user_model()
    team_size = User.objects.filter(department=user.department, role=User.Role.EMPLOYEE).count() if user.department else 0
    data['my_team_size'] = team_size
    return data


def manager_dashboard(user):
    data = {}
    User = get_user_model()
    today = timezone.localdate()
    team_size = User.objects.filter(department=user.department, role=User.Role.EMPLOYEE).count() if user.department else 0
    data['my_team_size'] = team_size
    on_leave = Attendance.objects.filter(employee__department=user.department, status='Leave', date=today).count() if user.department else 0
    data['employees_on_leave'] = on_leave
    pending = LeaveRequest.objects.filter(employee__department=user.department, status=LeaveRequest.Status.PENDING).count() if user.department else 0
    data['pending_leave_requests'] = pending
    first_of_month = today.replace(day=1)
    new_hires = User.objects.filter(department=user.department, date_joined__gte=first_of_month).count() if user.department else 0
    data['new_hires_this_month'] = new_hires
    from django.db.models import Avg
    avg_score = PerformanceReview.objects.filter(employee__department=user.department).aggregate(avg=Avg('overall_score'))['avg'] or 0
    data['team_avg_performance_score'] = round(avg_score, 2)
    reviews_month = PerformanceReview.objects.filter(employee__department=user.department, created_at__gte=first_of_month).count() if user.department else 0
    data['performance_reviews_this_month'] = reviews_month
    return data


def ceo_dashboard(user):
    data = {}
    User = get_user_model()
    today = timezone.localdate()
    now = timezone.now()
    first_of_month = today.replace(day=1)
    from datetime import timedelta
    last_30 = now - timedelta(days=30)

    total_users = User.objects.filter(deleted_at__isnull=True).count()
    employees = User.objects.filter(role=User.Role.EMPLOYEE).count()
    managers = User.objects.filter(role=User.Role.MANAGER).count()
    hr_count = User.objects.filter(role=User.Role.HR).count()
    data['headcount'] = {
        'total_active_users': total_users,
        'employees': employees,
        'managers': managers,
        'hr': hr_count,
    }

    dept_counts = []
    for dept in Department.objects.all():
        emp_count = User.objects.filter(department=dept, deleted_at__isnull=True).count()
        dept_counts.append({'id': dept.id, 'name': dept.name, 'emp_count': emp_count})
    data['departments'] = dept_counts

    hires_this_month = User.objects.filter(date_joined__date__gte=first_of_month).count()
    data['hires_this_month'] = hires_this_month

    deleted_last_30 = User.all_objects.filter(deleted_at__gte=last_30).count()
    previous_period_baseline = total_users + deleted_last_30 if (total_users + deleted_last_30) else 1
    attrition_rate = deleted_last_30 / previous_period_baseline
    data['attrition_last_30_days'] = {
        'count': deleted_last_30,
        'rate': round(attrition_rate, 4)
    }

    pending_leave = LeaveRequest.objects.pending().count()
    approved_leave_today = LeaveRequest.objects.approved().filter(start_date__lte=today, end_date__gte=today).count()
    data['leave'] = {
        'pending_requests': pending_leave,
        'employees_on_approved_leave_today': approved_leave_today,
    }

    from django.db.models import Avg, Max
    perf_qs = PerformanceReview.objects.all()
    avg_score = perf_qs.aggregate(avg=Avg('overall_score'))['avg'] or 0
    reviews_this_month = perf_qs.filter(created_at__date__gte=first_of_month).count()
    top_performers = (
        perf_qs.values('employee__id', 'employee__first_name', 'employee__last_name')
        .annotate(max_score=Max('overall_score'))
        .order_by('-max_score')[:5]
    )
    data['performance'] = {
        'average_score': round(avg_score, 2),
        'reviews_this_month': reviews_this_month,
        'top_performers': list(top_performers),
    }

    # Age distribution
    ages = []
    for dob in User.objects.filter(date_of_birth__isnull=False).values_list('date_of_birth', flat=True):
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        ages.append(age)
    buckets = {'<25':0,'25-34':0,'35-44':0,'45-54':0,'55+':0}
    for a in ages:
        if a < 25:
            buckets['<25'] += 1
        elif a < 35:
            buckets['25-34'] += 1
        elif a < 45:
            buckets['35-44'] += 1
        elif a < 55:
            buckets['45-54'] += 1
        else:
            buckets['55+'] += 1
    data['age_distribution'] = buckets

    return data


def build_dashboard(user):
    role = getattr(user, 'role', None)
    if role == getattr(user.__class__, 'Role').EMPLOYEE:
        return employee_dashboard(user)
    if role == getattr(user.__class__, 'Role').MANAGER:
        return manager_dashboard(user)
    if role == getattr(user.__class__, 'Role').CEO:
        return ceo_dashboard(user)
    # HR/ADMIN: show CEO view for now
    return ceo_dashboard(user)
