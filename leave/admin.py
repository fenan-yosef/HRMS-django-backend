from django.contrib import admin
from .models import LeaveRequest, LeaveType, LeaveBalance, LeaveApproval


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'start_date', 'end_date', 'status', 'applied_date')
    list_filter = ('status', 'start_date', 'end_date', 'leave_type')
    search_fields = ('employee__first_name', 'employee__last_name', 'reason')


@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'default_allowance_days', 'requires_approval')
    search_fields = ('code', 'name')


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'leave_type', 'year', 'allowance', 'used')
    list_filter = ('year', 'leave_type')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')


@admin.register(LeaveApproval)
class LeaveApprovalAdmin(admin.ModelAdmin):
    list_display = ('leave_request', 'approver', 'decision', 'approved_at')
    list_filter = ('decision',)
