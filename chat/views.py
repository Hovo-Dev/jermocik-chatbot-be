from rest_framework import generics, status
from django.shortcuts import get_object_or_404

from .models import Conversation, Message
from .serializers import (
    ConversationListSerializer,
    ConversationDetailSerializer,
    ConversationCreateSerializer,
    MessageSerializer,
    MessageCreateSerializer,
)
from core.responses import APIResponse
from core.mixins import AuthMixin
from .services import process_message_with_llm

class ConversationCreateView(AuthMixin, generics.CreateAPIView):
    """
    POST /api/v1/chat/conversations/
    Create a new conversation for the authenticated user.
    """
    serializer_class = ConversationCreateSerializer

    def perform_create(self, serializer):
        """Create conversation with the authenticated user."""
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """Override create to return proper response format."""
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            self.perform_create(serializer)
            
            # Return the created conversation with list serializer
            response_serializer = ConversationListSerializer(serializer.instance)
            
            return APIResponse.created(
                data=response_serializer.data,
                message="Conversation created successfully"
            )
        
        return APIResponse.error(
            message="Conversation creation failed",
            errors=serializer.errors,
            error_code="CONVERSATION_CREATION_FAILED",
            status_code=status.HTTP_400_BAD_REQUEST
        )


class ConversationListView(AuthMixin, generics.ListAPIView):
    """
    GET /api/v1/chat/conversations/list/
    List all conversations for the authenticated user.
    Returns only title, is_archived, and user_id fields.
    """
    serializer_class = ConversationListSerializer

    def get_queryset(self):
        """Return conversations for the authenticated user."""
        return Conversation.objects.filter(user=self.request.user).order_by('-last_message_at', '-created_at')

    def list(self, request, *args, **kwargs):
        """Override list to return proper response format."""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        return APIResponse.success(
            data=serializer.data,
            message="Conversations retrieved successfully"
        )


class ConversationDetailView(AuthMixin, generics.RetrieveAPIView):
    """
    GET /api/v1/chat/conversations/{conversation_id}/
    Retrieve a specific conversation with all its messages.
    """
    serializer_class = ConversationDetailSerializer

    def get_queryset(self):
        """Return conversations for the authenticated user."""
        return Conversation.objects.filter(user=self.request.user)

    def get_object(self):
        """Get conversation by ID, ensuring user ownership."""
        conversation_id = self.kwargs.get('conversation_id')

        return get_object_or_404(
            self.get_queryset(),
            id=conversation_id
        )

    def retrieve(self, request, *args, **kwargs):
        """Override retrieve to return proper response format."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        return APIResponse.success(
            data=serializer.data,
            message="Conversation retrieved successfully"
        )


class ConversationUpdateView(AuthMixin, generics.UpdateAPIView):
    """
    PATCH /api/v1/chat/conversations/{conversation_id}/
    Update conversation title or archive status.
    """
    serializer_class = ConversationListSerializer

    def get_queryset(self):
        """Return conversations for the authenticated user."""
        return Conversation.objects.filter(user=self.request.user)

    def get_object(self):
        """Get conversation by ID, ensuring user ownership."""
        conversation_id = self.kwargs.get('conversation_id')
        return get_object_or_404(
            self.get_queryset(),
            id=conversation_id
        )

    def update(self, request, *args, **kwargs):
        """Override update to return proper response format."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        if serializer.is_valid():
            self.perform_update(serializer)
            
            return APIResponse.success(
                data=serializer.data,
                message="Conversation updated successfully"
            )
        
        return APIResponse.error(
            message="Conversation update failed",
            errors=serializer.errors,
            error_code="CONVERSATION_UPDATE_FAILED",
            status_code=status.HTTP_400_BAD_REQUEST
        )


class ConversationDeleteView(AuthMixin, generics.DestroyAPIView):
    """
    DELETE /api/v1/chat/conversations/{conversation_id}/
    Delete a conversation and all its messages.
    """

    def get_queryset(self):
        """Return conversations for the authenticated user."""
        return Conversation.objects.filter(user=self.request.user)

    def get_object(self):
        """Get conversation by ID, ensuring user ownership."""
        conversation_id = self.kwargs.get('conversation_id')
        return get_object_or_404(
            self.get_queryset(),
            id=conversation_id
        )

    def destroy(self, request, *args, **kwargs):
        """Override destroy to return proper response format."""
        instance = self.get_object()
        self.perform_destroy(instance)
        
        return APIResponse.success(
            message="Conversation deleted successfully",
            status_code=status.HTTP_204_NO_CONTENT
        )


class ConversationMessagesView(AuthMixin, generics.ListAPIView):
    """
    GET /api/v1/chat/conversations/{conversation_id}/messages/
    Retrieve all messages for a specific conversation.
    Returns messages ordered by creation time (oldest first).
    """
    serializer_class = MessageSerializer

    def get_queryset(self):
        """Return messages for the specified conversation ordered by creation time."""
        conversation_id = self.kwargs.get('conversation_id')
        
        # Ensure the conversation belongs to the authenticated user
        conversation = get_object_or_404(
            Conversation.objects.filter(user=self.request.user),
            id=conversation_id
        )
        
        # Order by creation time (oldest first) for chronological chat display
        return Message.objects.filter(conversation=conversation).order_by('created_at')

    def list(self, request, *args, **kwargs):
        """Override list to return proper response format."""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        return APIResponse.success(
            data=serializer.data,
            message="Messages retrieved successfully"
        )


class MessageCreateView(AuthMixin, generics.CreateAPIView):
    """
    POST /api/v1/chat/conversations/{conversation_id}/messages/create/
    Create a new user message in a conversation and get AI response.
    """
    serializer_class = MessageCreateSerializer

    def get_conversation(self):
        """Get conversation by ID, ensuring user ownership."""
        conversation_id = self.kwargs.get('conversation_id')
        
        return get_object_or_404(
            Conversation.objects.filter(user=self.request.user),
            id=conversation_id
        )

    def perform_create(self, serializer):
        """Create user message with conversation and user context."""
        conversation = self.get_conversation()

        serializer.save(
            conversation=conversation,
            message_type='user'
        )

    def create(self, request, *args, **kwargs):
        """Override create to handle message creation and AI response."""
        try:
            # Validate conversation exists and user has access
            conversation = self.get_conversation()
            
            # Validate and create user message
            serializer = self.get_serializer(data=request.data)
            
            if not serializer.is_valid():
                return APIResponse.error(
                    message="Message creation failed",
                    errors=serializer.errors,
                    error_code="MESSAGE_CREATION_FAILED",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            # Create the initial user message
            self.perform_create(serializer)
            user_message = serializer.instance

            # Process message with LLM using service functions
            llm_result = process_message_with_llm(
                user_message=user_message.content,
                conversation=conversation,
            )

            # Create assistant message with LLM response
            assistant_message = Message.objects.create(
                conversation=conversation,
                content=llm_result['response'],
                message_type='assistant'
            )

            return APIResponse.created(
                data={
                    'assistant_message': MessageSerializer(assistant_message).data,
                },
                message="Message created and AI response generated successfully"
            )
            
        except Exception as e:
            return APIResponse.error(
                message="Failed to process message",
                errors={"detail": str(e)},
                error_code="MESSAGE_PROCESSING_FAILED",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
