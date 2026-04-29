from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache
from unittest.mock import patch
from core_db_ai.models import AIReport, Property, Agent

User = get_user_model()


class AIReportViewSetTests(APITestCase):
    """
    Test suite for AIReportViewSet covering:
    1. Staff vs Non-staff access (list vs my-reports)
    2. Daily limit & Global limit rate limiting (Cache)
    3. Celery task triggering and error handling
    4. Report ownership and deletion
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email="user@test.com",
            username="regularuser",
            password="password123",
            slug="regular-user",
        )
        self.other_user = User.objects.create_user(
            email="other@test.com",
            username="otheruser",
            password="password123",
            slug="other-user",
        )
        self.staff_user = User.objects.create_user(
            email="staff@test.com",
            username="staffuser",
            password="password123",
            is_staff=True,
            slug="staff-user",
        )
        self.superuser = User.objects.create_superuser(
            email="admin@test.com",
            username="admin",
            password="password123",
            slug="admin-user",
        )

        self.agent = Agent.objects.create(user=self.user, company_name="Test Agency")
        self.property = Property.objects.create(
            agent=self.agent,
            title="Modern Condo",
            address="123 AI Street, Tech City",
            beds=2,
            baths=2,
            price=300000,
            area_sqft=1200,
            slug="modern-condo",
        )

        self.list_url = reverse("report-list")
        self.my_reports_url = reverse("report-my-reports")

    def get_detail_url(self, pk):
        """Helper to generate retrieve/destroy URLs dynamically."""
        return reverse("report-detail", kwargs={"pk": pk})

    def tearDown(self):
        cache.clear()

    # --- LIST TESTS ---

    def test_list_reports_unauthorized(self):
        """Test 401: Unauthorized Access for List All Reports."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_reports_as_staff_success(self):
        """Test: Staff can access all reports via list."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_reports_as_user_forbidden(self):
        """Test: Non-staff users cannot access the main list."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["error"], "Only staff users can access this endpoint."
        )

    ## need test cases for my_reports function

    # --- RETRIEVE TESTS ---

    def test_my_reports_unauthorized(self):
        """Test 401: Unauthorized Access for My Reports."""
        response = self.client.get(self.my_reports_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_my_reports_as_user_success(self):
        """Test: Users can access their own reports."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.my_reports_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_my_report_not_found(self):
        """Test: 404 when report ID does not exist in my reports."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("aireport-detail", kwargs={"pk": 9999}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_report_ownership(self):
        """Test: Users can only retrieve their own reports."""
        report = AIReport.objects.create(user=self.other_user, property=self.property)
        self.client.force_authenticate(user=self.user)

        url = reverse("aireport-detail", kwargs={"pk": report.pk})
        response = self.client.get(url)
        # In your ViewSet, get_queryset filters by user, so this will be 404
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # --- CREATE & RATE LIMIT TESTS ---

    @patch("core_db_ai.views.parallel_report_generator.delay")
    def test_create_report_success(self, mock_task):  #! need work
        """Test: Successful creation triggers celery and sets user/global locks."""
        self.client.force_authenticate(user=self.user)
        payload = {"property_id": self.property.id}

        response = self.client.post(self.list_url, payload)

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn("is being generated", response.data["success"])

        # Verify DB entry
        report = AIReport.objects.filter(user=self.user, property=self.property).first()
        self.assertIsNotNone(report)

        # Verify Locks
        self.assertTrue(cache.get(f"user_report_lock:{self.user.id}"))
        self.assertEqual(int(cache.get("global_report_lock")), 1)

        # Verify Celery Trigger
        mock_task.assert_called_once()

    def test_create_report_unauthorized(self):
        """Test 401: Anonymous users cannot create reports."""
        response = self.client.post(self.list_url, {"property_id": self.property.id})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_report_as_staff_forbidden(self):
        """Test 403: Staff users (not superusers) cannot create reports."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(self.list_url, {"property_id": self.property.id})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["error"], "You do not have permission to create a report."
        )

    def test_create_report_missing_property_id(self):
        """Test 400: Error when property_id is missing from request."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.list_url, {})  # Empty payload

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Property ID is required.")

    def test_create_report_user_lock_active(self):
        """Test: 429 error when user daily limit is reached."""
        self.client.force_authenticate(user=self.user)
        cache.set(f"user_report_lock:{self.user.id}", "locked", timeout=60)

        response = self.client.post(self.list_url, {"property_id": self.property.id})
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn("Daily limit reached", response.data["error"])

    def test_create_report_global_lock_active(self):
        """Test: 429 error when system global limit (4) is reached."""
        self.client.force_authenticate(user=self.user)
        cache.set("global_report_lock", 4, timeout=60)

        response = self.client.post(self.list_url, {"property_id": self.property.id})
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn("System daily limit reached", response.data["error"])

    def test_create_report_property_not_found(self):
        """Test: 404 if property_id is invalid."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.list_url, {"property_id": 9999})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("Property not found", response.data["error"])

    @patch("core_db_ai.views.parallel_report_generator.delay")  #! need work
    def test_create_report_celery_exception_cleanup(self, mock_task):
        """Test: 500 error triggers lock release and report deletion if Celery fails."""
        mock_task.side_effect = Exception("Broker Connection Error")
        self.client.force_authenticate(user=self.user)

        response = self.client.post(self.list_url, {"property_id": self.property.id})

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        # Verify cleanup
        self.assertFalse(AIReport.objects.filter(user=self.user).exists())
        self.assertIsNone(cache.get(f"user_report_lock:{self.user.id}"))

    def test_create_report_duplicate_exists_error(self):
        """Test 400: Block creation if a non-failed report already exists."""
        AIReport.objects.create(
            user=self.user, property=self.property, status=AIReport.Status.COMPLETED
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.post(self.list_url, {"property_id": self.property.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already exists", response.data["error"])

    @patch("core_db_ai.views.parallel_report_generator.delay")
    def test_create_report_replaces_failed_report(self, mock_task):
        """Test: If an existing report is FAILED, delete it and create a new one."""
        old_failed_report = AIReport.objects.create(
            user=self.user, property=self.property, status=AIReport.Status.FAILED
        )
        old_id = old_failed_report.id

        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.list_url, {"property_id": self.property.id})

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        # Verify old report is gone
        self.assertFalse(AIReport.objects.filter(id=old_id).exists())
        # Verify new report exists
        self.assertTrue(
            AIReport.objects.filter(user=self.user, property=self.property).exists()
        )

    @patch("core_db_ai.views.parallel_report_generator.delay")
    def test_create_report_as_superuser_success(self, mock_task):
        """Test: Superusers bypass the staff-block and can create reports."""
        self.client.force_authenticate(user=self.superuser)
        response = self.client.post(self.list_url, {"property_id": self.property.id})

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    #! internal server error 500

    # --- DELETE (DESTROY) TESTS ---

    def test_delete_report_owner_success(self):
        """Test 200: Owner can delete their own report and receives custom message."""
        report = AIReport.objects.create(user=self.user, property=self.property)
        report_id = report.id

        self.client.force_authenticate(user=self.user)
        url = self.get_detail_url(report.pk)

        response = self.client.delete(url)

        # Verify custom 200 OK instead of DRF's default 244
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["success"],
            f"Report with ID {report_id} deleted successfully.",
        )
        self.assertFalse(AIReport.objects.filter(pk=report_id).exists())

    def test_delete_report_unauthenticated(self):
        """Test 401: Anonymous users cannot delete reports."""
        report = AIReport.objects.create(user=self.user, property=self.property)
        url = self.get_detail_url(report.pk)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["error"], "You are not authenticated.")

    def test_delete_report_not_found(self):
        """Test 404: Returns error when report ID does not exist."""
        self.client.force_authenticate(user=self.user)
        url = self.get_detail_url(9999)  # Non-existent ID

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_report_forbidden_for_other_user(self):
        """Test 403: User A cannot delete User B's report."""
        # Report owned by 'other_user'
        report = AIReport.objects.create(user=self.other_user, property=self.property)

        # Authenticate as 'user'
        self.client.force_authenticate(user=self.user)
        url = self.get_detail_url(report.pk)

        response = self.client.delete(url)

        # This triggers your 'if report_to_delete.user != current_user' logic
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["error"], "You are not authorized to delete this report."
        )

    def test_delete_report_superuser_bypass(self):
        """Test 200: Superuser can delete any user's report."""
        report = AIReport.objects.create(user=self.user, property=self.property)

        self.client.force_authenticate(user=self.superuser)
        url = self.get_detail_url(report.pk)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("deleted successfully", response.data["success"])
        self.assertFalse(AIReport.objects.filter(pk=report.pk).exists())
