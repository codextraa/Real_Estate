from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    OpenApiParameter,
    extend_schema,
)
from backend_ai.renderers import ViewRenderer
from backend_ai.schema_serializers import (
    ErrorResponseSerializer,
    ChatMessageGETResponseSerializer,
    ChatMessageRequestSerializer,
    ChatMessagePOSTResponseSerializer,
)
from core_db_ai.models import ChatSession, AIReport, ChatMessage
from .serializers import ChatSessionSerializer, ChatMessageSerializer
from .tasks import generate_ai_chat_response


def check_request_data(data_id, current_user, method):  # pylint: disable=R0911
    """
    Check if the id for either report or session is valid
    """
    if not data_id:
        return Response(
            {"error": "ID is required."}, status=status.HTTP_400_BAD_REQUEST
        )

    if not str(data_id).isdigit():
        return Response(
            {"error": "Invalid ID format. Must be an integer."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if method == "GET":
        ai_report = AIReport.objects.filter(pk=data_id).first()

        if not ai_report:
            return Response(
                {"error": f"Report with ID {data_id} does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if ai_report.user != current_user and not current_user.is_superuser:
            return Response(
                {
                    "error": "You do not have permission to view this report's chat session."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if ai_report.status != AIReport.Status.COMPLETED:
            if ai_report.status == AIReport.Status.FAILED:
                return Response(
                    {"error": "Report has failed. Please create a new report."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                {"error": "Report has not been completed yet."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return {
            "ai_report": ai_report,
        }

    if method == "DELETE":
        session = ChatSession.objects.filter(pk=data_id).first()

        if not session:
            return Response(
                {"error": f"Chat session with ID {data_id} does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if session.user != current_user and not current_user.is_superuser:
            return Response(
                {"error": "Access denied. This session belongs to another user."},
                status=status.HTTP_403_FORBIDDEN,
            )

        return {
            "session": session,
        }

    return None


class ChatSessionView(APIView):
    """
    Chat Session View (GET, DELETE)
    """

    renderer_classes = [ViewRenderer]
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "delete"]

    @extend_schema(
        summary="Get a AI Chat Session",
        description=(
            "Returns the chat session of a specific property by ID "
            "along with it's chat messages"
        ),
        tags=["AI Chat Sessions"],
        parameters=[
            OpenApiParameter(
                name="id",
                type=int,
                location=OpenApiParameter.PATH,
                description="ID of a specific report to retrieve it's chat session",
                required=True,
            ),
        ],
        request=None,
        responses={
            status.HTTP_200_OK: ChatSessionSerializer,
            status.HTTP_400_BAD_REQUEST: ErrorResponseSerializer,
            status.HTTP_401_UNAUTHORIZED: ErrorResponseSerializer,
            status.HTTP_403_FORBIDDEN: ErrorResponseSerializer,
            status.HTTP_404_NOT_FOUND: ErrorResponseSerializer,
            status.HTTP_405_METHOD_NOT_ALLOWED: ErrorResponseSerializer,
        },
        examples=[
            OpenApiExample(
                name="Unauthorized Access",
                response_only=True,
                status_codes=["401"],
                value={"error": "You are not authenticated."},
            ),
            OpenApiExample(
                name="Not Found Error",
                response_only=True,
                status_codes=["404"],
                value={"error": "Report with ID 1 does not exist."},
            ),
            OpenApiExample(
                name="Report belongs to another user",
                response_only=True,
                status_codes=["403"],
                value={
                    "error": "You do not have permission to view this report's chat session."
                },
            ),
            OpenApiExample(
                name="Unfinished Report Error",
                response_only=True,
                status_codes=["400"],
                value={"error": "Report has not been completed yet."},
            ),
            OpenApiExample(
                name="Failed Report Error",
                response_only=True,
                status_codes=["400"],
                value={"error": "Report has failed. Please create a new report."},
            ),
            OpenApiExample(
                name="Report ID Not Found Error",
                response_only=True,
                status_codes=["400"],
                value={"error": "ID is required."},
            ),
            OpenApiExample(
                name="Invalid Report ID Error",
                response_only=True,
                status_codes=["400"],
                value={"error": "Invalid ID format. Must be an integer."},
            ),
        ],
    )
    def get(self, request, *args, **kwargs):
        """
        Get Chat Session with it's messages
        """
        current_user = request.user

        report_id = kwargs.get("id")

        check_integrity = check_request_data(report_id, current_user, "GET")

        if isinstance(check_integrity, Response):
            return check_integrity

        session, created = ChatSession.objects.get_or_create(
            report=check_integrity["ai_report"],
            user=current_user,
        )

        if not created:
            session = ChatSession.objects.prefetch_related("messages").get(
                pk=session.pk
            )

        serializer = ChatSessionSerializer(session)
        return Response(
            data=serializer.data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="Delete an AI Chat Session",
        description=(
            "Deletes the chat session of a specific property by ID "
            "along with it's chat messages"
        ),
        tags=["AI Chat Sessions"],
        parameters=[
            OpenApiParameter(
                name="id",
                type=int,
                location=OpenApiParameter.PATH,
                description="ID of a specific chat session",
                required=True,
            ),
        ],
        request=None,
        responses={
            status.HTTP_200_OK: ChatSessionSerializer,
            status.HTTP_400_BAD_REQUEST: ErrorResponseSerializer,
            status.HTTP_401_UNAUTHORIZED: ErrorResponseSerializer,
            status.HTTP_403_FORBIDDEN: ErrorResponseSerializer,
            status.HTTP_404_NOT_FOUND: ErrorResponseSerializer,
        },
        examples=[
            OpenApiExample(
                name="Success Response",
                response_only=True,
                status_codes=["200"],
                value={
                    "success": "Chat history deleted successfully.",
                },
            ),
            OpenApiExample(
                name="Unauthorized Access",
                response_only=True,
                status_codes=["401"],
                value={"error": "You are not authenticated."},
            ),
            OpenApiExample(
                name="No Chat Session Error",
                response_only=True,
                status_codes=["404"],
                value={"error": "Chat session with ID 1 does not exist."},
            ),
            OpenApiExample(
                name="Unauthorized Chat access Error",
                response_only=True,
                status_codes=["403"],
                value={"error": "Access denied. This session belongs to another user."},
            ),
            OpenApiExample(
                name="Report ID Not Found Error",
                response_only=True,
                status_codes=["400"],
                value={"error": "ID is required."},
            ),
            OpenApiExample(
                name="Invalid Report ID Error",
                response_only=True,
                status_codes=["400"],
                value={"error": "Invalid ID format. Must be an integer."},
            ),
        ],
    )
    def delete(self, request, *args, **kwargs):
        """
        Delete Chat Session (needs to be seperated)
        """
        current_user = request.user

        session_id = kwargs.get("id")

        check_integrity = check_request_data(session_id, current_user, "DELETE")

        if isinstance(check_integrity, Response):
            return check_integrity

        session = check_integrity["session"]

        session.delete()

        return Response(
            {"success": "Chat history deleted successfully."},
            status=status.HTTP_200_OK,
        )


class ChatMessageDetailView(APIView):
    """
    Chat Message View (GET by ID)
    """

    renderer_classes = [ViewRenderer]
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = ["get"]

    @extend_schema(
        summary="Get an AI Chat Messages",
        description=("Returns a chat message of a specific session by ID."),
        tags=["AI Chat Messages"],
        parameters=[
            OpenApiParameter(
                name="id",
                type=int,
                location=OpenApiParameter.PATH,
                description="The ID of the specific message to retrieve",
                required=True,
            ),
        ],
        request=None,
        responses={
            status.HTTP_200_OK: ChatMessageGETResponseSerializer,
            status.HTTP_202_ACCEPTED: OpenApiResponse(
                response={
                    "type": "object",
                    "properties": {"pending": {"type": "string"}},
                },
            ),
            status.HTTP_401_UNAUTHORIZED: ErrorResponseSerializer,
            status.HTTP_403_FORBIDDEN: ErrorResponseSerializer,
            status.HTTP_404_NOT_FOUND: ErrorResponseSerializer,
            status.HTTP_405_METHOD_NOT_ALLOWED: ErrorResponseSerializer,
        },
        examples=[
            OpenApiExample(
                name="AI message still processing",
                response_only=True,
                status_codes=["202"],
                value={"pending": "Your message is still being processing."},
            ),
            OpenApiExample(
                name="Unauthorized Access",
                response_only=True,
                status_codes=["401"],
                value={"error": "You are not authenticated."},
            ),
            OpenApiExample(
                name="Not Found Error",
                response_only=True,
                status_codes=["404"],
                value={"error": "Message with ID 1 does not exist."},
            ),
            OpenApiExample(
                name="Unauthorized Chat access Error",
                response_only=True,
                status_codes=["403"],
                value={"error": "Access denied. You do not own this chat session."},
            ),
            OpenApiExample(
                name="Message ID Not Found Error",
                response_only=True,
                status_codes=["400"],
                value={"error": "Message ID is required."},
            ),
            OpenApiExample(
                name="Invalid Message ID Error",
                response_only=True,
                status_codes=["400"],
                value={"error": "Invalid Message ID format. Must be an integer."},
            ),
        ],
    )
    def get(self, request, *args, **kwargs):
        message_id = kwargs.get("id")
        current_user = request.user

        if not message_id:
            return Response(
                {"error": "Message ID is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        if not str(message_id).isdigit():
            return Response(
                {"error": "Invalid Message ID format. Must be an integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            message = ChatMessage.objects.select_related("session__user").get(
                pk=message_id
            )
        except ChatMessage.DoesNotExist:
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
                {"pending": f"Your message is still being {message.status.lower()}."},
                status=status.HTTP_202_ACCEPTED,
            )

        serializer = ChatMessageSerializer(message)

        return Response(
            {"success": "Message retrieved successfully.", "data": serializer.data},
            status=status.HTTP_200_OK,
        )


class ChatMessageCreateView(APIView):
    """
    Chat Message View (POST)
    """

    renderer_classes = [ViewRenderer]
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = ["post"]

    @extend_schema(
        summary="Post a User message for an AI response",
        description=(
            "Accepts a user message, creates a placeholder for the AI, "
            "and starts background processing."
        ),
        tags=["AI Chat Messages"],
        request=ChatMessageRequestSerializer,
        responses={
            status.HTTP_202_ACCEPTED: ChatMessagePOSTResponseSerializer,
            status.HTTP_400_BAD_REQUEST: ErrorResponseSerializer,
            status.HTTP_401_UNAUTHORIZED: ErrorResponseSerializer,
            status.HTTP_403_FORBIDDEN: ErrorResponseSerializer,
            status.HTTP_404_NOT_FOUND: ErrorResponseSerializer,
        },
        examples=[
            OpenApiExample(
                name="Session Not Found",
                response_only=True,
                status_codes=["404"],
                value={"error": "The specified ChatSession does not exist."},
            ),
            OpenApiExample(
                name="Forbidden Access",
                response_only=True,
                status_codes=["403"],
                value={"error": "Access denied. This session belongs to another user."},
            ),
        ],
    )
    def post(self, request, *args, **kwargs):
        """
        Post a user message and generate an AI response.
        """
        current_user = request.user
        session_id = request.data.get("session")
        user_content = request.data.get("content")

        try:
            session = ChatSession.objects.select_related("report").get(pk=session_id)

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

        generate_ai_chat_response.delay(ai_message.id, session.report_id, user_content)

        return Response(
            {
                "success": "Message is currently processing.",
                "data": {
                    "ai_message_id": ai_message.id,
                },
            },
            status=status.HTTP_202_ACCEPTED,
        )
