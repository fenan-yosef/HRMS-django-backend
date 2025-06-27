# hr_system/admin.py

from django.contrib import admin
from .models import Employee, Department, Payroll, Leave, PerformanceReview

# The admin.site.register() function tells the Django admin site to create
# an interface for the model you pass it.

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    """
    Admin view for Departments.
    """
    list_display = ('name', 'location')
    search_fields = ('name', 'location')

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    """
    Admin view for Employees. Provides a more detailed view in the admin panel.
    """
    list_display = ('first_name', 'last_name', 'job_title', 'department', 'status', 'manager')
    list_filter = ('status', 'department', 'job_title')
    search_fields = ('first_name', 'last_name', 'email', 'job_title')
    # This makes the manager selection field a searchable dropdown instead of a giant list
    raw_id_fields = ('manager',)


@admin.register(Payroll)
class PayrollAdmin(admin.ModelAdmin):
    """
    Admin view for Payroll.
    """
    list_display = ('employee', 'pay_period_start', 'pay_period_end', 'net_salary', 'payment_date')
    list_filter = ('payment_date',)
    search_fields = ('employee__first_name', 'employee__last_name')


@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    """
    Admin view for Leave requests.
    """
    list_display = ('employee', 'leave_type', 'start_date', 'end_date', 'status')
    list_filter = ('status', 'leave_type')
    search_fields = ('employee__first_name', 'employee__last_name')


@admin.register(PerformanceReview)
class PerformanceReviewAdmin(admin.ModelAdmin):
    """
    Admin view for Performance Reviews.
    """
    list_display = ('employee', 'reviewer', 'review_date', 'rating')
    list_filter = ('rating', 'review_date')
    search_fields = ('employee__first_name', 'employee__last_name', 'reviewer__first_name')

