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
        serializer = self.get_serializer(data=request.data)
        # Validate input
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as ve:
            return Response(
                {'errors': ve.detail},
                status=status.HTTP_400_BAD_REQUEST
            )
        # Attempt to create user
        try:
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(
                {
                    'message': 'User registered successfully.',
                    'user': serializer.data
                },
                status=status.HTTP_201_CREATED,
                headers=headers
            )
        except Exception as exc:
            return Response(
                {'errors': {'detail': f'Failed to register user: {str(exc)}'}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class LoginView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        try:
            identifier = request.data.get('identifier')  # Can be username or email
            password = request.data.get('password')
            if not identifier or not password:
                return Response(
                    {'errors': {'detail': 'Both identifier (username/email) and password are required.'}},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Determine if identifier is an email or username
            if '@' in identifier:
                user = authenticate(request, email=identifier, password=password)
            else:
                user = authenticate(request, username=identifier, password=password)

            if not user:
                return Response(
                    {'errors': {'detail': 'Invalid username/email or password.'}},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            login(request, user)
            return Response(
                {
                    'message': 'Login successful.',
                    'username': user.username,
                    'email': user.email,
                    'role': user.role
                },
                status=status.HTTP_200_OK
            )
        except Exception as exc:
            return Response(
                {'errors': {'detail': f'An unexpected error occurred: {str(exc)}'}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
