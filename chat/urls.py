from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    # Conversation endpoints
    path('conversations/', views.ConversationCreateView.as_view(), name='conversation-create'),
    path('conversations/list/', views.ConversationListView.as_view(), name='conversation-list'),
    path('conversations/<int:conversation_id>/', views.ConversationDetailView.as_view(), name='conversation-detail'),
    path('conversations/<int:conversation_id>/update/', views.ConversationUpdateView.as_view(), name='conversation-update'),
    path('conversations/<int:conversation_id>/delete/', views.ConversationDeleteView.as_view(), name='conversation-delete'),
    
    # Message endpoints
    path('conversations/<int:conversation_id>/messages/', views.ConversationMessagesView.as_view(), name='conversation-messages'),
    path('conversations/<int:conversation_id>/messages/create/', views.MessageCreateView.as_view(), name='message-create'),
]
