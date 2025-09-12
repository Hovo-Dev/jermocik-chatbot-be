from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
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
            'phone_number', 'is_verified', 'created_at', 'updated_at',
            'password', 'password_confirm'
        ]
        read_only_fields = ['id', 'is_verified', 'created_at', 'updated_at']
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
            'full_name', 'phone_number', 'is_verified', 'created_at'
        ]
        read_only_fields = ['id', 'username', 'email', 'is_verified', 'created_at']

class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        """Validate user credentials."""
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(username=email, password=password)

            if not user:
                raise serializers.ValidationError('Invalid credentials.')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')

            attrs['user'] = user
        else:
            raise serializers.ValidationError('Must include email and password.')

        return attrs
