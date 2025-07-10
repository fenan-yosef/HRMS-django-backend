# filepath: department/serializers.py
from rest_framework import serializers
from .models import Department
from employee.models import Employee


class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ['id', 'first_name', 'last_name']  # Include relevant fields


class DepartmentSerializer(serializers.ModelSerializer):
    """Serializer for Department model."""
    manager = EmployeeSerializer(read_only=True)  # Use EmployeeSerializer for the manager field

    class Meta:
        model = Department
        fields = '__all__'