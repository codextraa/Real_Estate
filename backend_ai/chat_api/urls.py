from django.urls import path
from .views import ChatSessionView, ChatMessageView

urlpatterns = [
    path('chat/session/<int:report_id>/', ChatSessionView.as_view(), name='chat-session'),
    path('chat/message/<int:message_id>/', ChatMessageView.as_view(), name='chat-message-detail'),
    path('chat/message/', ChatMessageView.as_view(), name='chat-message-create'),
]