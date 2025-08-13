from rest_framework import serializers
from .models import LeaveRequest
from hr.models import CustomUser

class LeaveRequestSerializer(serializers.ModelSerializer):
    employee = serializers.PrimaryKeyRelatedField(read_only=True)
    employee_details = serializers.SerializerMethodField()
    approvers = serializers.SerializerMethodField()

    class Meta:
        model = LeaveRequest
        fields = '__all__'
        extra_fields = ['approvers']

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
