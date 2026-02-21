from rest_framework import serializers
from chat_api.serializers import ChatMessageSerializer


class ErrorResponseSerializer(serializers.Serializer):  # pylint: disable=W0223
    """Standard error response structure (HTTP 400, 429, 500)."""

    error = serializers.CharField(
        help_text="A descriptive error message explaining the failure or status."
    )


class AIReportRequestSerializer(serializers.Serializer):  # pylint: disable=W0223
    """AI Report request serializer for report creation."""

    property_id = serializers.IntegerField(required=True)


class ChatMessageGETResponseSerializer(serializers.Serializer):  # pylint: disable=W0223
    """
    Standard success response for a Chat Message.
    Wraps the ChatMessage data and includes a success message.
    """

    success = serializers.CharField(default="Message retrieved successfully.")
    data = ChatMessageSerializer()

    class Meta:
        fields = ["success", "data"]


class ChatMessageRequestSerializer(serializers.Serializer):  # pylint: disable=W0223
    """Request body for creating a new chat message."""

    session = serializers.IntegerField(help_text="The ID of the Chat Session.")
    content = serializers.CharField(help_text="The message content from the user.")


class ChatMessageAIMessageSerializer(serializers.Serializer):  # pylint: disable=W0223
    """The data object returned upon successful message acceptance."""

    ai_message_id = serializers.IntegerField(
        help_text="The ID of the generated AI message placeholder."
    )


class ChatMessagePOSTResponseSerializer(
    serializers.Serializer
):  # pylint: disable=W0223
    """Wrapper for a 202 ACCEPTED response."""

    success = serializers.CharField(default="Message is currently processing.")
    data = ChatMessageAIMessageSerializer()
