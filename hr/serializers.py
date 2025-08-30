from rest_framework import serializers
from .models import CustomUser, PerformanceReview, Attendance, Complaint
from department.serializers import DepartmentSerializer
from department.models import Department
from django.contrib.auth import get_user_model, authenticate
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(
        max_length=254,
        required=True,
        validators=[
            UniqueValidator(queryset=User.objects.all(), message="A user with that email already exists.")
        ],
    )

    class Meta:
        model = User
        fields = ('email', 'password', 'role', 'first_name', 'last_name', 'phone_number', 'job_title', 'date_of_birth', 'department')

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data.get('email'),
            password=validated_data['password'],
            role=validated_data.get('role', 'employee'),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone_number=validated_data.get('phone_number', ''),
            job_title=validated_data.get('job_title', ''),
            date_of_birth=validated_data.get('date_of_birth', None),
            department=validated_data.get('department', None)
        )
        return user

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    # Write-only field for setting department by primary key
    department_id = serializers.PrimaryKeyRelatedField(write_only=True, source='department', queryset=Department.objects.all(), required=False)
    # Read-only nested representation of department
    department = DepartmentSerializer(read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'role', 'password', 'first_name', 'last_name',
            'phone_number', 'is_active', 'job_title', 'date_of_birth',
            # allow setting department via pk
            'department_id',
            'department'
        ]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name', 'manager', 'code', 'description']


class PerformanceReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerformanceReview
        fields = '__all__'

class AttendanceSerializer(serializers.ModelSerializer):
    total_hours = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Attendance
        fields = '__all__'
        read_only_fields = ['work_duration']

    def get_total_hours(self, obj):
        if obj.work_duration:
            return round(obj.work_duration.total_seconds() / 3600, 2)
        return None

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims to the actual JWT token
        token['username'] = user.username
        token['email'] = user.email
        token['role'] = user.role

        return token

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        if email and password:
            user = authenticate(request=self.context.get("request"), username=email, password=password)
            if not user:
                raise serializers.ValidationError("Invalid email or password.")
        else:
            raise serializers.ValidationError("Must include 'email' and 'password'.")

        data = super().validate(attrs)
        data['email'] = self.user.email
        data['role'] = self.user.role
        return data

class HighLevelUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'role']


class ComplaintSerializer(serializers.ModelSerializer):
    created_by = HighLevelUserSerializer(read_only=True)
    target_user_detail = HighLevelUserSerializer(source='target_user', read_only=True)

    class Meta:
        model = Complaint
        fields = [
            'id', 'type', 'subject', 'description', 'created_by', 'target_user',
            'target_user_detail', 'send_to_ceo', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'status', 'created_at', 'updated_at']

    def validate(self, attrs):
        user = self.context['request'].user
        ctype = attrs.get('type')
        # Managers can only create manager_report; employees only employee_complaint
        role = str(getattr(user, 'role', '')).lower()
        if role == 'manager' and ctype != 'manager_report':
            raise serializers.ValidationError({'type': 'Managers can only create manager reports.'})
        if role == 'employee' and ctype != 'employee_complaint':
            raise serializers.ValidationError({'type': 'Employees can only create employee complaints.'})
        return attrs

    def create(self, validated_data):
        if 'created_by' not in validated_data:
            validated_data['created_by'] = self.context['request'].user
        return Complaint.objects.create(**validated_data)
