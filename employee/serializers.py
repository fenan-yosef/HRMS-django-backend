from rest_framework import serializers
from .models import Employee
from department.serializers import DepartmentSerializer
from department.models import Department  # Import Department model
from django.contrib.auth.hashers import make_password


class EmployeeSerializer(serializers.ModelSerializer):
    """Serializer for Employee model."""
    department = serializers.CharField(write_only=True, required=False)  # allow department update via pk
    # Keep the read representation
    department_details = DepartmentSerializer(source='department', read_only=True)

    class Meta:
        model = Employee
        fields = '__all__'
        extra_kwargs = {
            'password': {'write_only': True, 'required': False}
        }

    def create(self, validated_data):
        department_id = self.context['request'].data.get('department')
        department = Department.objects.get(pk=department_id)

        password = validated_data.pop('password', None)
        if password:
            validated_data['password'] = make_password(password)
        else:
            validated_data['password'] = make_password(Employee.DEFAULT_PASSWORD)

        validated_data.pop('department', None)  # Remove 'department' from validated_data
        employee = Employee.objects.create(department=department, **validated_data)
        return employee

    def update(self, instance, validated_data):
        # Pop the department field if provided
        department_id = validated_data.pop('department', None)
        if department_id is not None:
            instance.department = Department.objects.get(pk=department_id)

        # Update password if provided
        password = validated_data.pop('password', None)
        if password:
            instance.password = make_password(password)

        # Update all other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance
