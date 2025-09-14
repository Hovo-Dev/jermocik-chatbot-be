from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

# Get the custom user model, from settings.py AUTH_USER_MODEL not Django's default User
User = get_user_model()

class Conversation(models.Model):
    """Model representing a chat conversation."""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations')
    title = models.CharField(max_length=255, blank=True)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'conversations'
        verbose_name = 'Conversation'
        verbose_name_plural = 'Conversations'
        ordering = ['-last_message_at', '-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_archived']),
        ]

    def __str__(self):
        return f"Conversation {self.id} - {self.title or 'Untitled'}"

    def save(self, *args, **kwargs):
        # Set default title if not provided
        if not self.title:
            self.title = f"Conversation {self.id or 'New'}"

        super().save(*args, **kwargs)

    def get_message_count(self):
        """Return the number of messages in this conversation."""
        return self.messages.count()

    def update_last_message_time(self):
        """Update the last_message_at field with the latest message timestamp."""
        last_message = self.messages.order_by('-created_at').first()

        if last_message:
            self.last_message_at = last_message.created_at
            self.save(update_fields=['last_message_at'])


class Message(models.Model):
    """Model representing a message within a conversation."""
    
    MESSAGE_TYPES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    content = models.TextField()
    message_type = models.CharField(
        max_length=20,
        choices=MESSAGE_TYPES,
        default='user',
        help_text="Type of message (user, assistant, system)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'messages'
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
            models.Index(fields=['message_type']),
        ]

    def __str__(self):
        return f"Message {self.id} in Conversation {self.conversation_id}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Update conversation's last_message_at when a new message is created
        if is_new:
            self.conversation.update_last_message_time()

    def get_short_content(self, max_length=100):
        """Return truncated content for display purposes."""
        if len(self.content) <= max_length:
            return self.content

        return self.content[:max_length] + "..."
