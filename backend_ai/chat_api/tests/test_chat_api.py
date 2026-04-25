from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from core_db_ai.models import AIReport, ChatSession, Property, Agent

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

        # 3. Setup Reports with different statuses
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

        # 4. URL (Assuming name='chat-session-view' in urls.py)
        self.url_name = "chat-session"

    def get_url(self, id):
        return reverse(self.url_name, kwargs={"id": id})

    # --- GET METHOD TEST CASES ---

    def test_get_check_id_missing(self):
        """Test: check_request_data returns 404 if data_id is None/Empty."""
        self.client.force_authenticate(user=self.user)
        # Using the base path without an ID to trigger the 'if not data_id' branch
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
        # Create a report for a different user
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

        # Verify no session exists for this report yet
        self.assertFalse(
            ChatSession.objects.filter(
                report=self.completed_report, user=self.user
            ).exists()
        )

        response = self.client.get(self.get_url(self.completed_report.pk))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify the session was automatically created in the DB
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
        # Hitting a path where ID is missing (if URL allows)
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
        # Create a session belonging to another user
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
        # Create a session for 'other_user'
        other_session = ChatSession.objects.create(
            user=self.other_user, report=self.completed_report
        )
        # Authenticate as the admin
        self.client.force_authenticate(user=self.superuser)
        response = self.client.delete(self.get_url(other_session.pk))

        # Superuser should succeed (200 OK from the view)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(ChatSession.objects.filter(pk=other_session.pk).exists())

    def test_delete_check_success_logic(self):
        """Test: check_request_data returns dict and session is deleted."""
        # Use the session created in setUp
        self.client.force_authenticate(user=self.user)
        session_id = self.session.pk

        response = self.client.delete(self.get_url(session_id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["success"], "Chat history deleted successfully.")
        # Final database check
        self.assertFalse(ChatSession.objects.filter(pk=session_id).exists())

    def test_delete_unauthorized_user_access_error(self):
        """Test 401: User is not authenticated."""
        response = self.client.delete(self.get_url(self.session.pk))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


### chat message + task
