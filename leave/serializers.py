from rest_framework import serializers
from .models import LeaveRequest, LeaveType, LeaveApproval, LeaveBalance
from hr.models import CustomUser

class LeaveRequestSerializer(serializers.ModelSerializer):
    employee = serializers.PrimaryKeyRelatedField(read_only=True)
    employee_details = serializers.SerializerMethodField()
    approvers = serializers.SerializerMethodField()
    yearly_granted_days = serializers.SerializerMethodField()
    yearly_remaining_days = serializers.SerializerMethodField()
    system_annual_request_limit = serializers.SerializerMethodField()

    deleted_at = serializers.DateTimeField(read_only=True)
    leave_type = serializers.PrimaryKeyRelatedField(queryset=LeaveType.objects.all(), required=False, allow_null=True)
    duration_days = serializers.DecimalField(max_digits=6, decimal_places=2, required=False, allow_null=True)

    class Meta:
        model = LeaveRequest
    fields = '__all__'
    extra_fields = ['approvers', 'deleted_at']

    def get_employee_details(self, obj):
        return {
            "first_name": obj.employee.first_name,
            "last_name": obj.employee.last_name,
            "email": obj.employee.email,
        }

    def get_approvers(self, obj):
        return [
            {
                "id": u.id,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "email": u.email,
                "role": u.role,
            }
            for u in obj.get_approvers()
        ]

    def _get_current_year(self):
        from django.utils import timezone
        return timezone.now().year

    def get_yearly_granted_days(self, obj):
        """Return total approved leave days for the employee in the current year."""
        year = self._get_current_year()
        approved = LeaveRequest.objects.approved().filter(employee=obj.employee, start_date__year=year)
        # Sum duration_days; fall back to difference if duration missing
        total = 0
        for r in approved:
            if r.duration_days is not None:
                total += float(r.duration_days)
            else:
                total += (r.end_date - r.start_date).days + 1
        return total

    def get_yearly_remaining_days(self, obj):
        # Use system setting key 'annual_leave_request_max_days', default 15
        from core.models import SystemSetting
        max_days = SystemSetting.get_int('annual_leave_request_max_days', default=15)
        granted = self.get_yearly_granted_days(obj)
        remaining = max_days - granted
        return max(remaining, 0)

    def get_system_annual_request_limit(self, obj):
        from core.models import SystemSetting
        return SystemSetting.get_int('annual_leave_request_max_days', default=15)
