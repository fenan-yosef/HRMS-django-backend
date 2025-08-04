from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.exceptions import ValidationError
from django.contrib.auth import authenticate, login, get_user_model
from .serializers import RegisterSerializer
from rest_framework.permissions import AllowAny

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        import random
        import string
        from django.core.mail import send_mail
        from django.conf import settings

        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as ve:
            return Response({'errors': ve.detail}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data.copy()
        password = data.get('password')
        if not password:
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            data['password'] = password

        try:
            user = User.objects.create_user(
                username=data['username'],
                email=data['email'],
                password=password,
                role=data.get('role', 'Employee')
            )
            # Send email with password
            send_mail(
                subject="Welcome to HRMS - Your Account Details",
                message=f"Hello {user.username},\n\nYour account has been created.\nEmail: {user.email}\nPassword: {password}\nPlease change your password after first login.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            headers = self.get_success_headers(serializer.data)
            response_data = {
                'message': 'User registered successfully and email sent.',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role
                }
            }
            return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as exc:
            return Response({'errors': {'detail': f'Failed to register user: {str(exc)}'}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LoginView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        identifier = request.data.get('identifier')  # Can be email
        password = request.data.get('password')
        if not identifier or not password:
            return Response(
                {'errors': {'detail': 'Both identifier (email) and password are required.'}},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Authenticate using email
        user = authenticate(request, identifier=identifier, password=password)

        if not user:
            return Response(
                {'errors': {'detail': 'Invalid email or password.'}},
                status=status.HTTP_401_UNAUTHORIZED
            )

        login(request, user)
        return Response(
            {
                'message': 'Login successful.',
                'email': user.email,
                'role': user.role
            },
            status=status.HTTP_200_OK
        )
