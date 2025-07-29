from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from django.conf import settings
import random
from .password_reset_serializers import RequestPasswordResetSerializer, ResetPasswordSerializer
from .models import CustomUser, PasswordResetOTP

class RequestPasswordResetView(APIView):
    """Request password reset: send OTP to email."""
    permission_classes = []
    def post(self, request):
        serializer = RequestPasswordResetSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        email = serializer.validated_data['email']
        otp = f"{random.randint(100000, 999999)}"
        PasswordResetOTP.objects.create(email=email, otp=otp)
        send_mail(
            subject="Your Password Reset OTP",
            message=f"Your OTP for password reset is: {otp}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        return Response({"message": "OTP sent to email."})

class ResetPasswordView(APIView):
    """Reset password using OTP."""
    permission_classes = []
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']
        new_password = serializer.validated_data['new_password']
        try:
            otp_obj = PasswordResetOTP.objects.get(email=email, otp=otp, is_used=False)
        except PasswordResetOTP.DoesNotExist:
            return Response({"error": "Invalid OTP or email."}, status=status.HTTP_400_BAD_REQUEST)
        if otp_obj.is_expired():
            return Response({"error": "OTP has expired."}, status=status.HTTP_400_BAD_REQUEST)
        user = CustomUser.objects.filter(email=email).first()
        if not user:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        user.set_password(new_password)
        user.save()
        otp_obj.is_used = True
        otp_obj.save()
        return Response({"message": "Password reset successful."})
