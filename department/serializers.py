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
    head_count = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = '__all__'
        # head_count will be included automatically

    def get_head_count(self, obj):
        # Count users linked to this department
        return obj.custom_users.count()

    def validate_manager(self, value):
        if value and str(value.role).lower() != 'manager':
            raise serializers.ValidationError('Only users with the manager role can be assigned as department manager.')
        return value