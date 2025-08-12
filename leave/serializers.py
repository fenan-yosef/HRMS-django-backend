from rest_framework import serializers
from .models import LeaveRequest
from hr.models import CustomUser

class LeaveRequestSerializer(serializers.ModelSerializer):
    employee = serializers.PrimaryKeyRelatedField(read_only=True)
    employee_details = serializers.SerializerMethodField()

    class Meta:
        model = LeaveRequest
        fields = '__all__'

    def get_employee_details(self, obj):
        return {
            "first_name": obj.employee.first_name,
            "last_name": obj.employee.last_name,
            "email": obj.employee.email,
        }
