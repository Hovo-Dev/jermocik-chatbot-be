from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import login

from .models import User
from .serializers import UserSerializer, UserProfileSerializer, LoginSerializer
from core.responses import APIResponse

class RegisterView(generics.CreateAPIView):
    """API endpoint for user registration."""
    
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        """Register a new user."""
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            return APIResponse.created(
                data=UserProfileSerializer(user).data,
                message="User registered successfully."
            )

        return APIResponse.error(
            message="Registration failed.",
            errors=serializer.errors,
            error_code="REGISTRATION_FAILED",
            status_code=status.HTTP_400_BAD_REQUEST
        )

class LoginView(APIView):
    """API endpoint for user login."""
    
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """Authenticate user and create session."""
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data['user']

            login(request, user)

            return APIResponse.success(
                data=UserProfileSerializer(user).data,
                message="Login successful."
            )

        return APIResponse.error(
            message="Login failed.",
            errors=serializer.errors,
            error_code="LOGIN_FAILED",
            status_code=status.HTTP_400_BAD_REQUEST
        )

class LogoutView(APIView):
    """API endpoint for user logout."""
    
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """Logout the current user."""
        # In a simple implementation, we just return success
        # In production, you might want to invalidate tokens or sessions
        return APIResponse.success(message="Logout successful.")

class ProfileView(generics.RetrieveUpdateAPIView):
    """API endpoint for user profile management."""
    
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """Return the current user."""
        return self.request.user

    def retrieve(self, *args, **kwargs):
        """Get user profile."""
        user = self.get_object()
        serializer = self.get_serializer(user)

        return APIResponse.success(
            data=serializer.data,
            message="Profile retrieved successfully."
        )

    def update(self, request, *args, **kwargs):
        """Update user profile."""
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()

            return APIResponse.success(
                data=serializer.data,
                message="Profile updated successfully."
            )

        return APIResponse.error(
            message="Profile update failed.",
            errors=serializer.errors,
            error_code="PROFILE_UPDATE_FAILED",
            status_code=status.HTTP_400_BAD_REQUEST
        )
