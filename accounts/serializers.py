from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from .models import User

class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
    )
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'created_at', 'updated_at', 'password', 'password_confirm'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'password': {'write_only': True},
            'password_confirm': {'write_only': True},
        }

    def validate(self, attrs):
        """Validate password confirmation."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")
        return attrs

    def create(self, validated_data):
        """Create a new user."""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')

        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()

        return user

class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile (without sensitive data)."""
    
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'full_name', 'created_at'
        ]
        read_only_fields = ['id', 'username', 'email', 'created_at']

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer for customizing the JWT token response.
    """
    @classmethod
    def get_token(cls, user):
        """
        Add custom claims to the token.
        """
        token = super().get_token(user)
        token['username'] = user.username
        token['email'] = user.email

        return token

    def validate(self, attrs):
        """
        Customize the response to include user details.
        """
        data = super().validate(attrs)
        data['user'] = UserProfileSerializer(self.user).data

        return data
