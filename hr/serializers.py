from rest_framework import serializers
from .models import CustomUser, Department, PerformanceReview, Attendance, Employee  # Import Employee model
from django.contrib.auth import get_user_model, authenticate
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    username = serializers.CharField(
        max_length=150,
        validators=[
            UniqueValidator(queryset=User.objects.all(), message="A user with that username already exists.")
        ],
        required=True,
    )
    email = serializers.EmailField(
        max_length=254,
        required=True,
        validators=[
            UniqueValidator(queryset=User.objects.all(), message="A user with that email already exists.")
        ],
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'role')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email'),
            password=validated_data['password'],
            role=validated_data.get('role', 'Employee')
        )
        return user

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'role', 'password', 'first_name', 'last_name']

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
    class Meta:
        model = Attendance
        fields = '__all__'

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
            employee = None
            if not user:
                # Try to authenticate against the Employee model
                try:
                    employee = Employee.objects.get(email=email)
                    if employee and employee.check_password(password):
                        user = employee  # Set user to the employee instance
                    else:
                        employee = None
                except Employee.DoesNotExist:
                    employee = None

            if not user:
                raise serializers.ValidationError("Invalid email or password.")

            if isinstance(user, Employee):
                # If the user is an Employee, create a CustomUser instance for the token
                # This assumes that you want to use the CustomUser model for JWT
                # You might need to adjust this based on your specific requirements
                from .models import CustomUser
                try:
                    custom_user = CustomUser.objects.get(email=user.email)
                except CustomUser.DoesNotExist:
                    # Create a CustomUser for the employee if one doesn't exist
                    custom_user = CustomUser.objects.create_user(
                        email=user.email,
                        password=password,  # Consider generating a new password
                        # Set other fields as needed
                    )
                user = custom_user  # Use the CustomUser instance for token generation


        else:
            raise serializers.ValidationError("Must include 'email' and 'password'.")

        data = super().validate(attrs)
        data['email'] = self.user.email
        data['role'] = self.user.role
        return data
        data['role'] = self.user.role
        return data

class HighLevelUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'role']
