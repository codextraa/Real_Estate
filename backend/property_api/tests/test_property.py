from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from core_db.models import Agent, Property

User = get_user_model()

PROPERTY_LIST_URL = reverse("property-list")
PROPERTY_DETAIL_URL = lambda pk: reverse("property-detail", kwargs={"pk": pk})


class PropertyViewSetTests(APITestCase):
    """Tests for the PropertyViewSet covering CRUD and permission logic."""

    def setUp(self):
        self.password = "StrongP@ss123"

        # 1. Setup Users
        self.superuser = User.objects.create_superuser(
            email="super@test.com", username="admin", password=self.password
        )

        self.staff_user = User.objects.create_user(
            email="staff@test.com",
            username="staffuser",
            password=self.password,
            is_staff=True,
        )

        # Agent User and its Profile
        self.agent_user = User.objects.create_user(
            email="agent@test.com",
            username="agentuser",
            password=self.password,
            is_agent=True,
        )
        self.agent_profile = Agent.objects.create(
            user=self.agent_user, company_name="Test Realty Group"
        )

        # Another Agent (for cross-edit testing)
        self.other_agent_user = User.objects.create_user(
            email="otheragent@test.com",
            username="otheragent",
            password=self.password,
            is_agent=True,
        )
        self.other_agent_profile = Agent.objects.create(
            user=self.other_agent_user, company_name="Other Agent Co"
        )

        # Normal User (should not be able to create properties)
        self.normal_user = User.objects.create_user(
            email="normal@test.com", username="normal", password=self.password
        )

        # 2. Setup initial Property owned by self.agent_profile
        self.property = Property.objects.create(
            agent=self.agent_profile,
            title="Initial Property",
            description="Initial Description",
            beds=2,
            baths=1,
            price=250000.00,
            area_sqft=1200,
            address="456 Property Lane",
            slug="initial-property",
        )

        self.client = APIClient()

    def _authenticate(self, user):
        self.client.force_authenticate(user=user)

    def get_valid_property_data(self):
        """Standard valid data for creating/updating properties."""
        return {
            "title": "luxury apartment",
            "description": "A grand view of the city.",
            "beds": 3,
            "baths": 2,
            "price": 500000.00,
            "area_sqft": 2000,
            "address": "123 Sky Tower",
        }

    #### --- List -----------

    def test_list_properties_authenticated_user_allowed(self):
        """Test that any authenticated user can view the property list."""
        self._authenticate(self.normal_user)
        response = self.client.get(PROPERTY_LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)

        self._authenticate(self.superuser)
        response = self.client.get(PROPERTY_LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)

        self._authenticate(self.staff_user)
        response = self.client.get(PROPERTY_LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)

        self._authenticate(self.agent_user)
        response = self.client.get(PROPERTY_LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)

    def test_unauthorized_users_cannot_list_properties(self):
        """Test that an unauthenticated user cannot view the property list."""
        response = self.client.get(PROPERTY_LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    ###  ---retrieve ----

    def test_retrieve_authenticated_user_allowed(self):
        """Test that any authenticated user can retrieve a property."""
        self._authenticate(self.normal_user)
        url = PROPERTY_DETAIL_URL(self.property.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.property.id)

        self._authenticate(self.agent_user)
        url = PROPERTY_DETAIL_URL(self.property.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.property.id)

        self._authenticate(self.superuser)
        url = PROPERTY_DETAIL_URL(self.property.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.property.id)

        self._authenticate(self.staff_user)
        url = PROPERTY_DETAIL_URL(self.property.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.property.id)

    def test_retrieve_unauthorized_user_not_allowed(self):
        """Test that an unauthenticated user cannot retrieve a property."""
        url = PROPERTY_DETAIL_URL(self.property.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    ### ---- Create -----

    def test_create_property_as_agent_success(self):
        """Test that an agent can create a property listing."""
        self._authenticate(self.agent_user)
        payload = self.get_valid_property_data()

        response = self.client.post(PROPERTY_LIST_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Property.objects.get(id=response.data.get('id', 0)).title, "Luxury Apartment")

    def test_create_property_forbidden_for_normal_user(self):
        """Test that a user with is_agent=False cannot create a property."""
        self._authenticate(self.normal_user)
        payload = self.get_valid_property_data()

        response = self.client.post(PROPERTY_LIST_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # def test_agent_can_update_own_property(self):
    #     """Test that an agent can patch their own property."""
    #     self._authenticate(self.agent_user)
    #     url = PROPERTY_DETAIL_URL(self.property.id)
    #     payload = {"title": "Updated Title"}

    #     response = self.client.patch(url, payload)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.property.refresh_from_db()
    #     self.assertEqual(self.property.title, "Updated Title")

    # def test_agent_cannot_update_others_property(self):
    #     """Test that an agent cannot modify properties they don't own."""
    #     self._authenticate(self.other_agent_user)
    #     url = PROPERTY_DETAIL_URL(self.property.id)

    #     response = self.client.patch(url, {"title": "Hacked Title"})
    #     self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # def test_forbidden_fields_ignored_on_update(self):
    #     """Test that 'slug' and 'agent' fields cannot be changed via API."""
    #     self._authenticate(self.agent_user)
    #     url = PROPERTY_DETAIL_URL(self.property.id)
    #     payload = {"slug": "changed-slug", "title": "New Title"}

    #     response = self.client.patch(url, payload)
    #     # Your view explicitly checks for 'slug' in request.data and returns 403
    #     self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # def test_delete_property_as_owner(self):
    #     """Test agent can delete their own property."""
    #     self._authenticate(self.agent_user)
    #     url = PROPERTY_DETAIL_URL(self.property.id)

    #     response = self.client.delete(url)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK) # Your view returns 200 on success
    #     self.assertFalse(Property.objects.filter(id=self.property.id).exists())

    # def test_image_upload_validation_size(self):
    #     """Test that images over 2MB are rejected."""
    #     self._authenticate(self.agent_user)
    #     # Create a 3MB file
    #     large_img = SimpleUploadedFile("big.jpg", b"0" * 3 * 1024 * 1024, content_type="image/jpeg")

    #     payload = self.get_valid_property_data()
    #     payload['property_image'] = large_img

    #     # Use format='multipart' for file uploads
    #     response = self.client.post(PROPERTY_LIST_URL, payload, format='multipart')

    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertIn("Property image size should not exceed 2MB.", str(response.data))
