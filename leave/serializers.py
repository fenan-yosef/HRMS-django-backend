from rest_framework import serializers
from .models import LeaveRequest
from employee.serializers import EmployeeSerializer

class LeaveRequestSerializer(serializers.ModelSerializer):
    employee_details = EmployeeSerializer(source='employee', read_only=True)

    class Meta:
        model = LeaveRequest
        fields = '__all__'
