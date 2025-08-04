# filepath: department/serializers.py
from rest_framework import serializers
from .models import Department
from hr.models import CustomUser


class ManagerSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'first_name', 'last_name', 'email']


class DepartmentSerializer(serializers.ModelSerializer):
    """Serializer for Department model."""
    manager = ManagerSerializer(read_only=True)  # Use ManagerSerializer for the manager field

    class Meta:
        model = Department
        fields = '__all__'