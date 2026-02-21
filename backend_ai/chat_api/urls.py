from django.urls import path
from .views import ChatSessionView, ChatMessageDetailView, ChatMessageCreateView

urlpatterns = [
    path("chat/session/<int:id>/", ChatSessionView.as_view(), name="chat-session"),
    path(
        "chat/message/<int:id>/",
        ChatMessageDetailView.as_view(),
        name="chat-message-detail",
    ),
    path("chat/message/", ChatMessageCreateView.as_view(), name="chat-message-create"),
]
