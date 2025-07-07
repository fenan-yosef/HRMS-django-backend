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
                {'error': f'Failed to register user: {str(exc)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class LoginView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        try:
            username = request.data.get('username')
            password = request.data.get('password')
            if not username or not password:
                return Response(
                    {'error': 'Both username and password are required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user = authenticate(request, username=username, password=password)
            if not user:
                return Response(
                    {'error': 'Invalid username or password.'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            login(request, user)
            return Response(
                {
                    'message': 'Login successful.',
                    'username': user.username,
                    'role': user.role
                },
                status=status.HTTP_200_OK
            )
        except Exception as exc:
            return Response(
                {'error': f'An unexpected error occurred: {str(exc)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
