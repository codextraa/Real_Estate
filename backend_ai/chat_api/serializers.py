from rest_framework import serializers
from core_db_ai.models import ChatSession, ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    """
    Serializer for the individual messages (List Type)
    Used to get all messages for a specific session.
    """

    class Meta:
        model = ChatMessage
        fields = ["id", "session", "role", "status", "content", "timestamp"]
        read_only_fields = fields


class ChatSessionSerializer(serializers.ModelSerializer):
    """
    Serializer for a specific ChatSession (Retrieve Type)
    Includes basic session info and nests the messages within it.
    """

    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatSession
        fields = [
            "id",
            "user",
            "report",
            "messages",
            "user_message_count",
            "created_at",
        ]
        read_only_fields = fields
