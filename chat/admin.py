from django.contrib import admin
from .models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    """Admin configuration for Conversation model."""
    
    list_display = [
        'id',
        'title',
        'user',
        'is_archived',
        'message_count',
        'created_at',
        'updated_at',
        'last_message_at',
    ]
    list_filter = [
        'is_archived',
        'created_at',
        'last_message_at',
    ]
    search_fields = [
        'title',
        'user__email',
        'user__username',
    ]
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'last_message_at',
    ]
    ordering = ['-created_at']
    
    def message_count(self, obj):
        """Display the number of messages in the conversation."""
        return obj.get_message_count()
    message_count.short_description = 'Message Count'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Admin configuration for Message model."""
    
    list_display = [
        'id',
        'conversation',
        'message_type',
        'content',
        'short_content',
        'created_at',
        'updated_at',
    ]
    list_filter = [
        'message_type',
        'created_at',
    ]
    search_fields = [
        'content',
        'conversation__title',
        'conversation__user__email',
    ]
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
    ]
    ordering = ['-created_at']
    
    def short_content(self, obj):
        """Display truncated content for the message."""
        return obj.get_short_content(50)

    short_content.short_description = 'Content'
