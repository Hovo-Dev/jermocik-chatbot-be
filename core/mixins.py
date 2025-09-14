from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication


class AuthMixin:
    """
    A reusable mixin to enforce JWT authentication and permissions.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
