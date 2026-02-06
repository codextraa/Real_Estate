from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from backend_ai.renderers import ViewRenderer
from core_db_ai.models import ChatSession, AIReport
from .serializers import ChatSessionSerializer


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
