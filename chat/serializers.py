from rest_framework import serializers
from .models import Conversation, Message

class MessageSerializer(serializers.ModelSerializer):
    """Serializer for Message model."""
    
    short_content = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = [
            'id',
            'conversation',
            'content',
            'message_type',
            'created_at',
            'updated_at',
            'short_content',
        ]
        read_only_fields = ['id', 'conversation', 'created_at', 'updated_at']

    def get_short_content(self, obj):
        """Return truncated content for list views."""
        return obj.get_short_content()


class ConversationListSerializer(serializers.ModelSerializer):
    """Serializer for Conversation model in list views."""
    
    message_count = serializers.SerializerMethodField()
    user_id = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'id',
            'title',
            'is_archived',
            'user',
            'user_id',
            'created_at',
            'updated_at',
            'last_message_at',
            'message_count',
        ]
        read_only_fields = ['id', 'user', 'user_id', 'created_at', 'updated_at', 'last_message_at', 'message_count']

    def get_message_count(self, obj):
        """Return the number of messages in this conversation."""
        return obj.get_message_count()
    
    def get_user_id(self, obj):
        """Return the user ID for API compatibility."""
        return obj.user.id


class ConversationDetailSerializer(serializers.ModelSerializer):
    """Serializer for Conversation model in detail views."""
    
    messages = MessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()
    user_id = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'id',
            'title',
            'is_archived',
            'user',
            'user_id',
            'created_at',
            'updated_at',
            'last_message_at',
            'message_count',
            'messages',
        ]
        read_only_fields = ['id', 'user', 'user_id', 'created_at', 'updated_at', 'last_message_at', 'message_count', 'messages']

    def get_message_count(self, obj):
        """Return the number of messages in this conversation."""
        return obj.get_message_count()
    
    def get_user_id(self, obj):
        """Return the user ID for API compatibility."""
        return obj.user.id


class ConversationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new conversations."""
    
    class Meta:
        model = Conversation
        fields = ['title']
        
    def validate_title(self, value):
        """Validate title field."""
        if value and len(value.strip()) == 0:
            raise serializers.ValidationError("Title cannot be empty.")

        return value.strip() if value else None


class MessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new user messages."""
    
    class Meta:
        model = Message
        fields = ['content']
        
    def validate_content(self, value):
        """Validate content field."""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Message content cannot be empty.")
        
        if len(value.strip()) > 10000:  # Reasonable limit for message content
            raise serializers.ValidationError("Message content is too long. Maximum 10,000 characters allowed.")
            
        return value.strip()

