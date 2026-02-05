from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from backend_ai.renderers import ViewRenderer
from core_db_ai.models import ChatSession, AIReport
from .serializers import ChatSessionSerializer


class ChatSessionView(APIView):
    """
    Handles operations for a specific session: Retrieve and Delete.
    URL Pattern: /chat-sessions/<int:pk>/
    """

    renderer_classes = [ViewRenderer]
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def check_request_data(self, report_id, current_user):
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

    def get(self, request, report_id):
        current_user = request.user

        check_integrity = self.check_request_data(report_id, current_user)

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

        # 4. If it already existed, make sure we have the messages
        if not created:
            session = ChatSession.objects.prefetch_related("messages").get(
                pk=session.pk
            )

        # 6. Success (200 OK)
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
        Logic: Delete a specific session by its associated Report ID.
        Returns 200 OK to confirm message delivery.
        """
        current_user = request.user

        check_integrity = self.check_request_data(report_id, current_user)

        if check_integrity:
            return check_integrity

        # 4. Fetch the session or return 404 if no session exists
        try:
            # Look up by report_id to keep logic consistent with GET
            session = ChatSession.objects.get(report_id=report_id)

            # Check Ownership
            if session.user != current_user:
                return Response(
                    {"error": "Access denied. This session belongs to another user."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            # Perform deletion
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
