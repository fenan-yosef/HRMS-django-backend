from rest_framework import serializers
from .models import Employee
from department.serializers import DepartmentSerializer  # Import DepartmentSerializer


class EmployeeSerializer(serializers.ModelSerializer):
    """Serializer for Employee model."""
    department = DepartmentSerializer(read_only=True)  # Use DepartmentSerializer for the department field

    class Meta:
        model = Employee
        fields = '__all__'
