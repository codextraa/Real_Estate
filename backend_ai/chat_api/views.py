from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from backend_ai.renderers import ViewRenderer
from core_db_ai.models import ChatSession, AIReport, ChatMessage
from .serializers import ChatSessionSerializer, ChatMessageSerializer
from .tasks import generate_ai_response_task


def check_request_data(report_id, current_user):
    if not str(report_id).isdigit():
        return Response(
            {"error": "Invalid Report ID format. Must be an integer."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not AIReport.objects.filter(pk=report_id).exists():
        return Response(
            {"error": f"Report with ID {report_id} does not exist."},
            status=status.HTTP_404_NOT_FOUND,
        )

    if current_user.is_staff and not current_user.is_superuser:
        return Response(
            {"error": "You do not have permission to view this chat session."},
            status=status.HTTP_403_FORBIDDEN,
        )

    return None


class ChatSessionView(APIView):
    """
    Chat Session View (GET, DELETE)
    """

    renderer_classes = [ViewRenderer]
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, report_id):
        """
        Get Chat Session
        """
        current_user = request.user

        check_integrity = check_request_data(report_id, current_user)

        if check_integrity:
            return check_integrity

        session, created = ChatSession.objects.get_or_create(
            report=report_id,
            user=current_user.id,
        )

        if session.user != current_user:
            return Response(
                {"error": "Access denied. This session belongs to another user."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not created:
            session = ChatSession.objects.prefetch_related("messages").get(
                pk=session.pk
            )

        serializer = ChatSessionSerializer(session)
        return Response(
            {
                "success": "Chat history retrieved successfully.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request, report_id):
        """
        Delete Chat Session
        """
        current_user = request.user

        check_integrity = check_request_data(report_id, current_user)

        if check_integrity:
            return check_integrity

        try:
            session = ChatSession.objects.get(report_id=report_id)

            if session.user != current_user:
                return Response(
                    {"error": "Access denied. This session belongs to another user."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            session.delete()

            return Response(
                {"success": "Chat history deleted successfully."},
                status=status.HTTP_200_OK,
            )
        except ChatSession.DoesNotExist:
            return Response(
                {"error": f"No chat session exists for Report {report_id}."},
                status=status.HTTP_404_NOT_FOUND,
            )


class ChatMessageView(APIView):
    """
    Chat Message View (GET, POST)
    """

    renderer_classes = [ViewRenderer]
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, message_id):
        current_user = request.user
        message = ChatMessage.objects.get(pk=message_id)

        if not str(message_id).isdigit():
            return Response(
                {"error": "Invalid Message ID format. Must be an integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not message:
            return Response(
                {"error": f"Message with ID {message_id} does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if message.session.user != current_user:
            return Response(
                {"error": "Access denied. You do not own this chat session."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if message.status != ChatMessage.Status.COMPLETED:
            return Response(
                {"error": f"Your message is still being {message.status.lower()}."},
                status=status.HTTP_202_ACCEPTED,
            )
        serializer = ChatMessageSerializer(message)

        return Response(
            {"success": "Message retrieved successfully.", "data": serializer.data},
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        """
        Post a user message and generate an AI response.
        """
        current_user = request.user
        session_id = request.data.get("session")
        user_content = request.data.get("content")

        try:
            session = ChatSession.objects.get(pk=session_id)
            if session.user != current_user:
                return Response(
                    {"error": "Access denied. This session belongs to another user."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        except ChatSession.DoesNotExist:
            return Response(
                {"error": "The specified ChatSession does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )

        ChatMessage.objects.create(
            session=session,
            content=user_content,
            role=ChatMessage.Role.USER,
            status=ChatMessage.Status.COMPLETED,
        )

        ai_message = ChatMessage.objects.create(
            session=session, role=ChatMessage.Role.AI
        )

        # 3. Trigger Celery Task
        generate_ai_response_task.delay(
            ai_message.id, 
            session.report_id,
            user_content
        )

        # 3. Generate and Save AI Message
        # Note: Replace 'generate_ai_content' with your actual LLM logic/API call
        # ai_response_text = self.generate_ai_content(user_content)

        # 4. Return both messages
        return Response(
            {
                "success": "Message is currently processing.",
                "data": {
                    "ai_message_id": ai_message.id,
                },
            },
            status=status.HTTP_202_ACCEPTED,
        )
