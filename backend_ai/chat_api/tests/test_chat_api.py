from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from core_db_ai.models import AIReport, ChatSession, ChatMessage, Property, Agent
from django.core.cache import cache
from unittest.mock import patch


User = get_user_model()


class ChatSessionViewSetTests(APITestCase):
    """
    Comprehensive test suite covering:
    1. Validation logic (check_request_data)
    2. API Endpoint behavior (ChatSessionView GET/DELETE)
    3. Permissions and status constraints
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email="ariana@test.com",
            username="ariana",
            password="password123",
            first_name="Ariana",
            last_name="Suha",
            slug="ariana-suha",
        )
        self.other_user = User.objects.create_user(
            email="other@test.com",
            username="other",
            password="password123",
            slug="other-user",
        )
        self.superuser = User.objects.create_superuser(
            email="admin@test.com",
            username="admin",
            password="password123",
            slug="admin-user",
        )

        self.agent = Agent.objects.create(user=self.user, company_name="Codextra")
        self.property = Property.objects.create(
            agent=self.agent,
            title="Glass Box Estate",
            beds=3,
            baths=2,
            price=500000,
            area_sqft=2500,
            slug="glass-box-estate",
        )
        self.completed_report = AIReport.objects.create(
            user=self.user, property=self.property, status=AIReport.Status.COMPLETED
        )
        self.failed_report = AIReport.objects.create(
            user=self.user, property=self.property, status=AIReport.Status.FAILED
        )
        self.pending_report = AIReport.objects.create(
            user=self.user, property=self.property, status=AIReport.Status.PENDING
        )

        self.session = ChatSession.objects.create(
            user=self.user, report=self.completed_report
        )
        self.url_name = "chat-session"

    def get_url(self, id):
        return reverse(self.url_name, kwargs={"id": id})

    # --- GET METHOD TEST CASES ---

    def test_get_check_id_missing(self):
        """Test: check_request_data returns 404 if data_id is None/Empty."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/chat/session//")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_check_id_not_digit(self):
        """Test: check_request_data returns 404 for non-integer ID formats."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/chat/session/abc/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_check_report_not_found(self):
        """Test: check_request_data returns 404 if the AIReport pk doesn't exist."""
        self.client.force_authenticate(user=self.user)
        invalid_id = 99999
        response = self.client.get(self.get_url(invalid_id))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.data["error"], f"Report with ID {invalid_id} does not exist."
        )

    def test_get_check_permission_denied(self):
        """Test: check_request_data returns 403 if user doesn't own the report."""
        other_report = AIReport.objects.create(
            user=self.other_user,
            property=self.property,
            status=AIReport.Status.COMPLETED,
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.get_url(other_report.pk))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["error"],
            "You do not have permission to view this report's chat session.",
        )

    def test_get_check_status_failed(self):
        """Test: check_request_data returns 400 for reports with FAILED status."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.get_url(self.failed_report.pk))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error"], "Report has failed. Please create a new report."
        )

    def test_get_check_status_not_completed(self):
        """Test: check_request_data returns 400 for PENDING or PROCESSING reports."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.get_url(self.pending_report.pk))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Report has not been completed yet.")

    def test_get_session_success_and_creation(self):
        """Test 200: Successfully get (and create) a session for a completed report."""
        ChatSession.objects.filter(
            report=self.completed_report, user=self.user
        ).delete()
        self.client.force_authenticate(user=self.user)

        self.assertFalse(
            ChatSession.objects.filter(
                report=self.completed_report, user=self.user
            ).exists()
        )

        response = self.client.get(self.get_url(self.completed_report.pk))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            ChatSession.objects.filter(
                report=self.completed_report, user=self.user
            ).exists()
        )

    def test_get_session_unauthorized_user_access_error(self):
        """Test 401: Unauthorized Access (User not authenticated)."""
        response = self.client.get(self.get_url(self.completed_report.pk))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ## ---DELETE TESTS--- ##

    def test_delete_check_id_missing(self):
        """Test: check_request_data returns 400 if session_id is None."""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete("/api/chat/session//")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_check_id_not_digit(self):
        """Test: check_request_data returns 400 for non-integer session IDs."""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete("/api/chat/session/xyz/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_check_session_id_not_found(self):
        """Test: check_request_data returns 404 if the ChatSession doesn't exist."""
        self.client.force_authenticate(user=self.user)
        invalid_session_id = 88888
        response = self.client.delete(self.get_url(invalid_session_id))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.data["error"],
            f"Chat session with ID {invalid_session_id} does not exist.",
        )

    def test_delete_check_session_permission_denied(self):
        """Test: check_request_data returns 403 if user doesn't own the session."""
        other_session = ChatSession.objects.create(
            user=self.other_user, report=self.completed_report
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.get_url(other_session.pk))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["error"],
            "Access denied. This session belongs to another user.",
        )

    def test_delete_check_superuser_bypass(self):
        """Test: check_request_data allows superuser to delete others' sessions."""
        other_session = ChatSession.objects.create(
            user=self.other_user, report=self.completed_report
        )
        self.client.force_authenticate(user=self.superuser)
        response = self.client.delete(self.get_url(other_session.pk))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(ChatSession.objects.filter(pk=other_session.pk).exists())

    def test_delete_check_success_logic(self):
        """Test: check_request_data returns dict and session is deleted."""
        self.client.force_authenticate(user=self.user)
        session_id = self.session.pk

        response = self.client.delete(self.get_url(session_id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["success"], "Chat history deleted successfully.")
        self.assertFalse(ChatSession.objects.filter(pk=session_id).exists())

    def test_delete_unauthorized_user_access_error(self):
        """Test 401: User is not authenticated."""
        response = self.client.delete(self.get_url(self.session.pk))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ChatMessageTests(APITestCase):
    """
    Test suite for ChatMessage APIViews covering:
    1. Retrieval logic (Pending vs Completed)
    2. Message ownership and validation
    3. Rate limiting (User & Global locks)
    4. Celery task triggering and error cleanup
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email="user@test.com", username="user", password="password123", slug="user"
        )
        self.other_user = User.objects.create_user(
            email="other@test.com",
            username="other",
            password="password123",
            slug="other",
        )

        self.agent = Agent.objects.create(user=self.user, company_name="Codextra")
        self.property = Property.objects.create(
            agent=self.agent,
            title="Prop",
            price=100,
            area_sqft=10,
            beds=1,
            baths=1,
            slug="prop",
        )
        self.report = AIReport.objects.create(
            user=self.user, property=self.property, status=AIReport.Status.COMPLETED
        )

        self.session = ChatSession.objects.create(user=self.user, report=self.report)
        self.other_session = ChatSession.objects.create(
            user=self.other_user, report=self.report
        )

        # 4. URLs
        self.create_url = reverse("chat-message-create")

    def tearDown(self):
        cache.clear()

    def get_detail_url(self, msg_id):
        return reverse("chat-message-detail", kwargs={"id": msg_id})

    # --- ChatMessageDetailView (GET) ---

    def test_get_message_unauthorized(self):
        """Test 401: Anonymous user cannot retrieve messages."""
        msg = ChatMessage.objects.create(session=self.session, role=ChatMessage.Role.AI)
        response = self.client.get(self.get_detail_url(msg.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_message_success_completed(self):
        """Test 200: Retrieve a completed AI message."""
        msg = ChatMessage.objects.create(
            session=self.session,
            role=ChatMessage.Role.AI,
            status=ChatMessage.Status.COMPLETED,
            content="This is the AI response.",
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.get_detail_url(msg.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["content"], "This is the AI response.")

    def test_get_message_pending_processing(self):
        """Test 202: Message is still processing."""
        msg = ChatMessage.objects.create(
            session=self.session,
            role=ChatMessage.Role.AI,
            status=ChatMessage.Status.PROCESSING,
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.get_detail_url(msg.id))

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn("still being processing", response.data["pending"])

    def test_get_message_forbidden_ownership(self):
        """Test 403: Cannot view messages from a session owned by another user."""
        other_msg = ChatMessage.objects.create(
            session=self.other_session, role=ChatMessage.Role.USER
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.get_detail_url(other_msg.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["error"], "Access denied. You do not own this chat session."
        )

    def test_get_message_not_found(self):
        """Test 404: Requesting a non-existent message ID."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.get_detail_url(9999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_message_invalid_id_format_error(self):
        """
        Test 400: Sending 'abc' should trigger the view's custom error.
        We hardcode the URL to bypass reverse() validation.
        """
        self.client.force_authenticate(user=self.user)

        url = "/server-api-ai/chat-api/chat/message/abc/"
        response = self.client.get(url)
        self.assertIn(
            response.status_code,
            [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND],
        )

    def test_get_message_not_found(self):
        """
        Test 404: Sending a valid integer that doesn't exist in DB.
        We CAN use reverse() here because 99999 is a valid integer.
        """
        self.client.force_authenticate(user=self.user)
        url = reverse("chat-message-detail", kwargs={"id": 99999})

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    ### ChatMessageCreate Tests ---
    def test_post_message_unauthorized(self):
        """Test 401: Anonymous user cannot create messages."""
        response = self.client.post(
            self.create_url, {"session": self.session.id, "content": "Hi"}
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_message_session_not_found(self):
        """Test 404: The specified ChatSession does not exist."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.create_url, {"session": 9999, "content": "Hi"})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.data["error"], "The specified ChatSession does not exist."
        )

    def test_post_message_forbidden_access(self):
        """Test 403: Attempting to post to a session owned by another user."""
        self.client.force_authenticate(user=self.user)
        # Session belongs to self.other_user
        response = self.client.post(
            self.create_url, {"session": self.other_session.id, "content": "Hi"}
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["error"],
            "Access denied. This session belongs to another user.",
        )

    def test_post_message_user_rate_limit(self):
        """Test 429: User has reached their daily message limit (10)."""
        cache.set(f"user_chat_lock:{self.user.id}", 10)
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            self.create_url, {"session": self.session.id, "content": "Hi"}
        )

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn("Daily limit reached", response.data["error"])

    def test_post_message_global_rate_limit(self):
        """Test 429: Total system limit reached (100)."""
        cache.set("global_chat_lock", 100)
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            self.create_url, {"session": self.session.id, "content": "Hi"}
        )

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn("System daily limit reached", response.data["error"])

    # --- 500 Internal Server Error (Celery Task Trigger Failure) ---
    # @patch("core_db_ai.views.generate_ai_chat_response.delay")
    # def test_post_message_internal_server_error(self, mock_task):
    #     """Test 500: Failed to trigger AI task (simulated crash)."""
    #     # Mocking an exception during task.delay()
    #     mock_task.side_effect = Exception("Celery Connection Refused")

    #     self.client.force_authenticate(user=self.user)
    #     response = self.client.post(self.create_url, {"session": self.session.id, "content": "Hi"})

    #     self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    #     self.assertEqual(response.data["error"], "Failed to generate report. Please try again later.")

    #     # Verify cleanup: The AI placeholder message should have been deleted
    #     self.assertEqual(ChatMessage.objects.filter(role=ChatMessage.Role.AI).count(), 0)

    # --- 202 Accepted (Success Case) ---
    # @patch("core_db_ai.views.generate_ai_chat_response.delay")
    # def test_post_message_success(self, mock_task):
    #     """Test 202: Successful message creation and task handoff."""
    #     self.client.force_authenticate(user=self.user)
    #     payload = {"session": self.session.id, "content": "Analyze this property."}

    #     response = self.client.post(self.create_url, payload)

    #     self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
    #     self.assertIn("ai_message_id", response.data["data"])
    #     mock_task.assert_called_once()

    # --- 400 Bad Request (Session Message Limit) ---
    # def test_post_message_session_max_limit_reached(self):
    #     """
    #     Test 400: Session object tracks a max of 10 messages.
    #     Checks the 'if session.user_message_count >= 10' branch.
    #     """
    #     self.client.force_authenticate(user=self.user)

    #     # We mock the property 'user_message_count' to return 10
    #     with patch.object(ChatSession, 'user_message_count', new=10):
    #         payload = {"session": self.session.id, "content": "This should fail."}
    #         response = self.client.post(self.create_url, payload)

    #         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #         self.assertEqual(
    #             response.data["error"],
    #             "You have reached the maximum number of messages."
    #         )
