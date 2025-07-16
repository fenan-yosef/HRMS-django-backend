from rest_framework import serializers
from .models import Employee
from department.serializers import DepartmentSerializer
from department.models import Department  # Import Department model
from django.contrib.auth.hashers import make_password


class EmployeeSerializer(serializers.ModelSerializer):
    """Serializer for Employee model."""
    department = DepartmentSerializer(read_only=True)
    password = serializers.CharField(write_only=True, required=False, default=None)

    class Meta:
        model = Employee
        fields = '__all__'
        extra_kwargs = {
            'password': {'write_only': True, 'required': False}
        }

    def create(self, validated_data):
        department_id = self.context['request'].data.get('department')  # Get department ID from request data
        department = Department.objects.get(pk=department_id)  # Retrieve the Department instance
        
        password = validated_data.pop('password', None)
        if password:
            validated_data['password'] = make_password(password)
        else:
            validated_data['password'] = make_password(Employee.DEFAULT_PASSWORD)

        employee = Employee.objects.create(department=department, **validated_data)  # Create the Employee
        return employee

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        if password:
            instance.password = make_password(password)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance
