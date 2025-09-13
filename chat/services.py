"""
Chat services module for handling business logic related to conversations and messages.
This module contains functions for chat history retrieval, context processing, and LLM integration.
"""

from typing import List, Dict, Any, Optional

from .models import Conversation, Message


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
            'created_at': message.created_at.isoformat()
        })
    
    # Reverse to get chronological order (oldest first)
    return list(reversed(chat_history))


def retrieve_context_for_message(
    user_message: str, 
    chat_history: List[Dict[str, Any]], 
    conversation: Conversation
) -> Dict[str, Any]:
    """Retrieve context for user message. TODO: Implement actual retrieval logic."""
    return {
        'retrieved_documents': [],
        'relevant_conversations': [],
        'user_preferences': {},
        'knowledge_base_results': [],
        'context_metadata': {
            'retrieval_method': 'mock',
            'confidence_score': 0.0,
            'sources_count': 0
        }
    }


def call_llm_api(
    user_message: str,
    chat_history: List[Dict[str, Any]],
    context: Dict[str, Any],
    conversation: Conversation
) -> str:
    """Call LLM API. TODO: Implement actual LLM integration."""
    return f"Mock LLM response to: '{user_message[:50]}...'"


def format_prompt_for_llm(
    user_message: str,
    chat_history: List[Dict[str, Any]],
    context: Dict[str, Any],
    system_prompt: Optional[str] = None
) -> List[Dict[str, str]]:
    """Format prompt for LLM API calls."""
    messages = []
    
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    
    if context.get('retrieved_documents'):
        context_content = "Relevant context:\n"
        for doc in context['retrieved_documents']:
            context_content += f"- {doc.get('content', '')}\n"
        messages.append({"role": "system", "content": context_content})
    
    for message in chat_history[-10:]:
        messages.append({"role": message['role'], "content": message['content']})
    
    messages.append({"role": "user", "content": user_message})

    return messages


def get_system_prompt(user) -> str:
    """Get system prompt for LLM. TODO: Implement user-specific prompts."""
    return "You are a helpful AI assistant. Provide accurate, helpful, and concise responses based on the context provided. If you don't know something, say so rather than making up information."


def process_message_with_llm(
    user_message: str,
    conversation: Conversation,
    max_history: int = 20
) -> Dict[str, Any]:
    """Complete message processing pipeline."""
    chat_history = get_chat_history_for_llm(conversation, max_history)

    context = retrieve_context_for_message(user_message, chat_history, conversation)

    system_prompt = get_system_prompt(conversation.user)
    
    formatted_prompt = format_prompt_for_llm(
        user_message, chat_history, context, system_prompt
    )
    
    llm_response = call_llm_api(user_message, chat_history, formatted_prompt, conversation)
    
    return {
        'response': llm_response,
        'context_used': context,
        'history_count': len(chat_history),
        'processing_metadata': {
            'context_sources': context.get('context_metadata', {}).get('sources_count', 0),
            'confidence_score': context.get('context_metadata', {}).get('confidence_score', 0.0)
        }
    }
