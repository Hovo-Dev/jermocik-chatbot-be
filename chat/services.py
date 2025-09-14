"""
Chat services module for handling business logic related to conversations and messages.
This module contains functions for chat history retrieval, context processing, and LLM integration.
"""

from typing import List, Dict, Any, Optional

from .models import Conversation, Message
from responder.agents import run_responder

def get_chat_history_for_llm(conversation: Conversation, max_limit: int = 20) -> List[Dict[str, Any]]:
    """Get recent chat history for LLM context."""
    total_messages = Message.objects.filter(conversation=conversation).count()
    
    if total_messages == 0:
        return []

    limit = min(max_limit, total_messages)
    queryset = Message.objects.filter(conversation=conversation).order_by('-created_at')[:limit]
    
    # Convert Message objects to dict format expected by LLM
    chat_history = []
    for message in queryset:
        chat_history.append({
            'role': message.message_type,
            'content': message.content,
        })
    
    # Reverse to get chronological order (oldest first)
    return list(reversed(chat_history))


def process_message_with_llm(
    conversation: Conversation,
    max_history: int = 20
) -> Dict[str, Any]:
    """Complete message processing pipeline."""
    chat_history = get_chat_history_for_llm(conversation, max_history)

    llm_response = run_responder(chat_history)

    return llm_response