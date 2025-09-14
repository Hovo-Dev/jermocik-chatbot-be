from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenBlacklistView, TokenRefreshView

from .models import User
from .serializers import UserSerializer, UserProfileSerializer, CustomTokenObtainPairSerializer
from core.responses import APIResponse
from core.mixins import AuthMixin

class RegisterView(generics.CreateAPIView):
    """
    POST /api/v1/accounts/register/
    Register a new user account.
    """
    
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        """Register a new user and return JWT tokens."""
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)

            return APIResponse.created(
                data={
                    "user": UserProfileSerializer(user).data,
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
                message="User registered successfully."
            )

        return APIResponse.error(
            message="Registration failed.",
            errors=serializer.errors,
            error_code="REGISTRATION_FAILED",
            status_code=status.HTTP_400_BAD_REQUEST
        )

class LoginTokenObtainPairView(TokenObtainPairView):
    """
    POST /api/v1/accounts/login/
    Returns JWT access and refresh tokens upon successful login.
    """
    serializer_class = CustomTokenObtainPairSerializer

class LogoutView(TokenBlacklistView):
    """
    POST /api/v1/accounts/logout/
    Logout the current user and blacklist the refresh token.
    """
    pass

class RefreshTokenView(TokenRefreshView):
    """
    POST /api/v1/accounts/refresh-token/
    Refresh the access token using a valid refresh token.
    """
    pass

class ProfileView(AuthMixin, generics.RetrieveUpdateAPIView):
    """
    GET /api/v1/accounts/profile/
    PATCH /api/v1/accounts/profile/
    Retrieve or update the authenticated user's profile.
    """
    
    serializer_class = UserProfileSerializer

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
