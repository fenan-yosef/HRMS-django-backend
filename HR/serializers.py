# hr_system/serializers.py

from rest_framework import serializers
from .models import Employee, Department, Leave, PerformanceReview

# A serializer is like a DTO in NestJS. It defines the JSON representation 
# of your model and handles data validation.

class DepartmentSerializer(serializers.ModelSerializer):
    """
    Serializer for the Department model.
    """
    class Meta:
        model = Department
        fields = ['id', 'name', 'location'] # The fields to include in the JSON output

class EmployeeListSerializer(serializers.ModelSerializer):
    """
    A simplified serializer for listing employees. We don't want to show
    all details in a list view.
    """
    # This will display the department name instead of just the ID.
    department = serializers.StringRelatedField() 
    
    class Meta:
        model = Employee
        fields = ['id', 'first_name', 'last_name', 'job_title', 'email', 'department']

class EmployeeDetailSerializer(serializers.ModelSerializer):
    """
    A detailed serializer for a single employee view. Includes more fields
    and nested relationships.
    """
    # Nested serializers or StringRelatedField can show related data.
    department = DepartmentSerializer(read_only=True)
    
    # We can also show the manager's name instead of just their ID.
    # 'StringRelatedField' calls the __str__ method of the model.
    manager = serializers.StringRelatedField(read_only=True)

    # We can explicitly define fields for related objects that are not part of the model by default
    reports = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Employee
        # We specify all fields we want to expose in the detailed API endpoint.
        # Notice we exclude sensitive data like 'salary' by default.
        fields = [
            'id', 'first_name', 'last_name', 'date_of_birth', 'gender', 
            'email', 'phone_number', 'address', 'hire_date', 'job_title', 
            'status', 'department', 'manager', 'reports'
        ]

class LeaveSerializer(serializers.ModelSerializer):
    """
    Serializer for the Leave model.
    """
    # Shows the employee's name for readability
    employee = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Leave
        fields = '__all__' # Includes all fields from the Leave model

class PerformanceReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for the PerformanceReview model.
    """
    employee = serializers.StringRelatedField(read_only=True)
    reviewer = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = PerformanceReview
        fields = '__all__'

