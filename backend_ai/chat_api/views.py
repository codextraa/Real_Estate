# from django.shortcuts import get_object_or_404
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from rest_framework_simplejwt.authentication import JWTAuthentication
# from rest_framework.permissions import IsAuthenticated
# from core_db_ai.models import ChatSession
# from .serializers import ChatSessionSerializer, ChatMessageSerializer
# from backend.renderers import viewrenderer

# class ChatSessionView(APIView):
#     """
#     Handles operations for a specific session: Retrieve and Delete.
#     URL Pattern: /chat-sessions/<int:pk>/
#     """

#     renderer_classes = [viewrenderer]
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated]

#     def get(self, request, pk):
#         """
#         Retrieve chat session by ID with custom error handling.
#         """
#         current_user = request.user

#         # 2. Handle 400 Bad Request (Example: checking if PK is a valid integer)
#         if not str(pk).isdigit():
#             return Response(
#                 {"error": "Invalid Session ID format. Must be an integer."},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         # 3. Handle 403 Forbidden (Logic-based permission check)
#         # Example: Staff members are blocked from viewing user chats
#         if current_user.is_staff and not current_user.is_superuser:
#             return Response(
#                 {"error": "You do not have permission to view this chat session."},
#                 status=status.HTTP_403_FORBIDDEN
#             )

#         try:
#             # 4. Handle 404 Not Found (Checking existence and ownership)
#             # We fetch strictly by ID first to see if it exists at all
#             session = ChatSession.objects.prefetch_related('messages').get(pk=pk)

#             # Additional 403 check: If session exists but doesn't belong to the user
#             if session.user != current_user:
#                 return Response(
#                     {"error": "Access denied. This session belongs to another user."},
#                     status=status.HTTP_403_FORBIDDEN
#                 )

#         except ChatSession.DoesNotExist:
#             return Response(
#                 {"error": f"Chat session with ID {pk} not found."},
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         # 5. Handle 200 OK (Success)
#         serializer = ChatSessionSerializer(session)
#         return Response(
#             {
#                 "success": "Chat history retrieved successfully.",
#                 "data": serializer.data
#             },
#             status=status.HTTP_200_OK
#         )

#     def post(self, request):
#         """
#         Logic: Create a new chat session.
#         """
#         #user and report id input to model directly

#     def delete(self, request, pk):
#         """
#         Logic: Delete a specific session.
#         """
#         session = get_object_or_404(ChatSession, pk=pk, user=request.user)

#         # This deletes the session and all related ChatMessages via CASCADE
#         session.delete()

#         return Response(
#             {"detail": "Session deleted successfully."},
#             status=status.HTTP_204_NO_CONTENT
#         )
