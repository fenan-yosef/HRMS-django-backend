from rest_framework import serializers
from .models import LeaveRequest, LeaveType, LeaveApproval, LeaveBalance
from hr.models import CustomUser

class LeaveRequestSerializer(serializers.ModelSerializer):
    employee = serializers.PrimaryKeyRelatedField(read_only=True)
    employee_details = serializers.SerializerMethodField()
    approvers = serializers.SerializerMethodField()

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
