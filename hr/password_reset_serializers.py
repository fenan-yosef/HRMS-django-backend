from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import PasswordResetOTP
from .models import CustomUser

User = get_user_model()

class RequestPasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user with this email.")
        return value

class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField(min_length=8)

    def validate(self, data):
        email = data.get('email')
        otp = data.get('otp')
        try:
            otp_obj = PasswordResetOTP.objects.get(email=email, otp=otp, is_used=False)
        except PasswordResetOTP.DoesNotExist:
            raise serializers.ValidationError("Invalid OTP or email.")
        if otp_obj.is_expired():
            raise serializers.ValidationError("OTP has expired.")
        return data
