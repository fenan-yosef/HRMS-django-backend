from rest_framework import serializers
from .models import Employee
from department.serializers import DepartmentSerializer
from department.models import Department  # Import Department model


class EmployeeSerializer(serializers.ModelSerializer):
    """Serializer for Employee model."""
    department = DepartmentSerializer(read_only=True)

    class Meta:
        model = Employee
        fields = '__all__'

    def create(self, validated_data):
        department_id = self.context['request'].data.get('department')  # Get department ID from request data
        department = Department.objects.get(pk=department_id)  # Retrieve the Department instance
        employee = Employee.objects.create(department=department, **validated_data)  # Create the Employee
        return employee
