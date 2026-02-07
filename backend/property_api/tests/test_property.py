from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from core_db.models import Agent, Property

User = get_user_model()

PROPERTY_LIST_URL = reverse("property-list")
PROPERTY_DETAIL_URL = lambda pk: reverse("property-detail", kwargs={"pk": pk})
MY_LISTING_URL = reverse("property-my-listings")


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

    def dummy_properties(self):
        """Create some dummy properties for testing."""
        for i in range(15):
            Property.objects.create(
                title=f"Property {i}",
                description="Description",
                price=1000 + (i * 1000),
                beds=(i % 5) + 1,
                baths=(i % 5) + 1,
                area_sqft=1000 + (i * 1000),
                address=f"Street {i}",
                agent=self.agent_profile,
            )

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

    #### -------- LIST --------

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

    ####  -------- RETRIEVE --------

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

    #### -------- CREATE --------

    def test_create_property_as_agent_success(self):
        """Test that a user with is_agent=True can create a property."""
        self._authenticate(self.agent_user)
        payload = self.get_valid_property_data()
        response = self.client.post(PROPERTY_LIST_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        property_exists = Property.objects.filter(title="Luxury Apartment").first()
        self.assertTrue(property_exists)
        expected_property_slug = f"luxury-apartment-{property_exists.id}"
        self.assertEqual(property_exists.slug, expected_property_slug)

    def test_create_property_forbidden_for_other_users(self):
        """Test that a user with is_agent=False cannot create a property."""
        self._authenticate(self.normal_user)
        payload = self.get_valid_property_data()

        response = self.client.post(PROPERTY_LIST_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self._authenticate(self.staff_user)
        payload = self.get_valid_property_data()

        response = self.client.post(PROPERTY_LIST_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self._authenticate(self.superuser)
        payload = self.get_valid_property_data()

        response = self.client.post(PROPERTY_LIST_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_forbidden_field_cannot_be_update_while_creating(self):
        """Test that 'slug' and 'agent' fields cannot be changed."""
        self._authenticate(self.agent_user)
        payload = self.get_valid_property_data()
        payload["slug"] = "custom-slug"

        response = self.client.post(PROPERTY_LIST_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Forbidden fields cannot be updated.", response.data["error"])

        del payload["slug"]
        payload["agent"] = self.other_agent_user.id

        response = self.client.post(PROPERTY_LIST_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Forbidden fields cannot be updated.", response.data["error"])

    def test_property_title_length_exceeded(self):
        """Test that a property title cannot exceed 150 characters."""
        self._authenticate(self.agent_user)
        payload = self.get_valid_property_data()
        payload["title"] = "A" * 151

        response = self.client.post(PROPERTY_LIST_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "Ensure this field has no more than 150 characters.", response.data["title"]
        )

    def test_property_address_length_exceeded(self):
        """Test that a property address cannot exceed 255 characters."""
        self._authenticate(self.agent_user)
        payload = self.get_valid_property_data()
        payload["address"] = "A" * 256

        response = self.client.post(PROPERTY_LIST_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "Ensure this field has no more than 255 characters.",
            response.data["address"],
        )

    def test_unauthorized_user_cannot_create_property(self):
        """Test that an unauthenticated user cannot create a property."""
        payload = self.get_valid_property_data()
        response = self.client.post(PROPERTY_LIST_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    #### -------- UPDATE --------

    def test_agent_can_update_own_property(self):
        """Test that an agent can patch their own property."""
        self._authenticate(self.agent_user)
        url = PROPERTY_DETAIL_URL(self.property.id)
        payload = {"title": "Updated Title"}

        response = self.client.patch(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.property.refresh_from_db()
        self.assertEqual(self.property.title, "Updated Title")
        self.assertEqual(self.property.slug, f"updated-title-{self.property.id}")

    def test_other_user_or_agent_cannot_update_others_property(self):
        """Test that others users or agents cannot modify properties they don't own."""
        self._authenticate(self.normal_user)
        url = PROPERTY_DETAIL_URL(self.property.id)

        response = self.client.patch(url, {"title": "Hacked Title"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self._authenticate(self.other_agent_user)
        url = PROPERTY_DETAIL_URL(self.property.id)

        response = self.client.patch(url, {"title": "Hacked Title"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_staff_and_superuser_cannot_update_any_property(self):
        """Test that staff and superuser cannot modify any property."""
        self._authenticate(self.staff_user)
        url = PROPERTY_DETAIL_URL(self.property.id)

        response = self.client.patch(url, {"title": "Hacked Title"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["error"],
            "You do not have permission to update this property.",
        )

        self._authenticate(self.superuser)
        url = PROPERTY_DETAIL_URL(self.property.id)

        response = self.client.patch(url, {"title": "Hacked Title"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["error"],
            "You do not have permission to update this property.",
        )

    def test_forbidden_fields_error_on_update(self):
        """Test that 'slug' and 'agent' fields cannot be changed via API."""
        self._authenticate(self.agent_user)
        url = PROPERTY_DETAIL_URL(self.property.id)
        payload = {"slug": "changed-slug"}

        response = self.client.patch(url, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        payload = {"agent": self.other_agent_profile.id}

        response = self.client.patch(url, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_title_length_exceeded_on_update(self):
        """Test that a property title cannot exceed 150 characters."""
        self._authenticate(self.agent_user)
        url = PROPERTY_DETAIL_URL(self.property.id)
        payload = {"title": "A" * 151}

        response = self.client.patch(url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "Ensure this field has no more than 150 characters.",
            response.data["title"],
        )

    def test_address_length_exceeded_on_update(self):
        """Test that a property address cannot exceed 255 characters."""
        self._authenticate(self.agent_user)
        url = PROPERTY_DETAIL_URL(self.property.id)
        payload = {"address": "A" * 256}

        response = self.client.patch(url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "Ensure this field has no more than 255 characters.",
            response.data["address"],
        )

    def test_put_method_not_allowed(self):
        """Test that PUT returns 405 as it is excluded from http_method_names."""
        self._authenticate(self.agent_user)
        url = PROPERTY_DETAIL_URL(self.property.id)
        # Using the correct helper method name from your setup
        response = self.client.put(url, self.get_valid_property_data())
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_property_not_found(self):
        """Test updating a property ID that doesn't exist in the DB."""
        self._authenticate(self.agent_user)
        # Use an ID that is highly unlikely to exist
        url = PROPERTY_DETAIL_URL(99999)
        payload = {"title": "New Title"}

        response = self.client.patch(url, payload)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthorized_user_cannot_update_property(self):
        """Test that an unauthenticated user cannot update a property."""
        url = PROPERTY_DETAIL_URL(self.property.id)
        payload = {"title": "New Title"}

        response = self.client.patch(url, payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    #### -------- DELETE --------

    def test_delete_property_as_owner(self):
        """Test agent can delete their own property."""
        self._authenticate(self.agent_user)
        url = PROPERTY_DETAIL_URL(self.property.id)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Property.objects.filter(id=self.property.id).exists())

    def test_delete_any_property_as_superuser(self):
        """Superuser can delete a property."""
        self._authenticate(self.superuser)
        url = PROPERTY_DETAIL_URL(self.property.id)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Property.objects.filter(id=self.property.id).exists())

    def test_normal_user_other_agent_staff_cannot_delete_property(self):
        """Other users, agents and staffs cannot delete property"""
        self._authenticate(self.normal_user)
        url = PROPERTY_DETAIL_URL(self.property.id)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self._authenticate(self.other_agent_user)
        url = PROPERTY_DETAIL_URL(self.property.id)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self._authenticate(self.staff_user)
        url = PROPERTY_DETAIL_URL(self.property.id)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["error"],
            "You are not authorized to delete this property.",
        )

    def test_delete_property_not_found(self):
        """Test deleting a property ID that doesn't exist in the DB."""
        self._authenticate(self.agent_user)
        url = PROPERTY_DETAIL_URL(99999)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthorized_user_cannot_delete_property(self):
        """Test that an unauthenticated user cannot delete a property."""
        url = PROPERTY_DETAIL_URL(self.property.id)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    #### -------- MY LISTING TESTS --------

    def test_my_listings_action_success(self):
        """Test the @action 'my-listings' returns only current agent properties."""
        Property.objects.create(
            agent=self.other_agent_profile,
            title="Other Agent Prop",
            description="Another description required by full_clean",
            beds=1,
            baths=1,
            price=100000.00,
            area_sqft=800,
            address="789 Side Street",
            slug="other-agent-prop",
        )

        self._authenticate(self.agent_user)
        response = self.client.get(MY_LISTING_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], self.property.id)

    def test_other_users_staff_superuser_cannot_use_my_listings(self):
        """Other users, agents and staffs cannot use my-listings action"""
        self._authenticate(self.normal_user)
        response = self.client.get(MY_LISTING_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["error"],
            "Only users with an agent profile can access this endpoint.",
        )

        self._authenticate(self.staff_user)
        response = self.client.get(MY_LISTING_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["error"],
            "Only users with an agent profile can access this endpoint.",
        )

        self._authenticate(self.superuser)
        response = self.client.get(MY_LISTING_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["error"],
            "Only users with an agent profile can access this endpoint.",
        )

    def test_my_listing_action_not_authenticated(self):
        response = self.client.get(MY_LISTING_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    #### -------- PAGINATION TESTS --------

    def test_pagination_first_page(self):
        """Test that the first page returns the correct page size."""
        self.dummy_properties()
        self._authenticate(self.agent_user)

        response = self.client.get(PROPERTY_LIST_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 12)
        self.assertEqual(response.data["count"], 16)
        self.assertEqual(response.data["total_pages"], 2)
        self.assertIsNotNone(response.data["next"])

        response = self.client.get(MY_LISTING_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 12)
        self.assertEqual(response.data["count"], 16)
        self.assertEqual(response.data["total_pages"], 2)
        self.assertIsNotNone(response.data["next"])

    def test_pagination_second_page(self):
        """Test that the second page contains the remaining items."""
        self.dummy_properties()
        self._authenticate(self.agent_user)

        response = self.client.get(PROPERTY_LIST_URL, {"page": 2})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 4)
        self.assertEqual(response.data["count"], 16)
        self.assertEqual(response.data["total_pages"], 2)
        self.assertIsNone(response.data["next"])

        response = self.client.get(MY_LISTING_URL, {"page": 2})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 4)
        self.assertEqual(response.data["count"], 16)
        self.assertEqual(response.data["total_pages"], 2)
        self.assertIsNone(response.data["next"])

    #### -------- FILTER TESTS --------

    def test_filter_by_beds_and_baths(self):
        """Test filtering by exact bed and bath count."""
        self.dummy_properties()
        self._authenticate(self.agent_user)

        response = self.client.get(PROPERTY_LIST_URL, {"beds": 1})
        self.assertEqual(response.data["count"], 3)

        response = self.client.get(PROPERTY_LIST_URL, {"baths": 2})
        self.assertEqual(response.data["count"], 3)

        response = self.client.get(MY_LISTING_URL, {"beds": 1})
        self.assertEqual(response.data["count"], 3)

        response = self.client.get(MY_LISTING_URL, {"baths": 2})
        self.assertEqual(response.data["count"], 3)

    def test_filter_beds_and_baths_gte_8(self):
        """Test the '8+' logic in filter_beds_and_baths."""
        self._authenticate(self.agent_user)
        Property.objects.create(
            title="Mansion",
            description="A grand view of the city.",
            price=100000,
            beds=10,
            baths=10,
            area_sqft=5000,
            address="Rich St",
            agent=self.agent_profile,
        )

        response = self.client.get(PROPERTY_LIST_URL, {"beds": "8+"})
        self.assertEqual(len(response.data["results"]), 1)

        response = self.client.get(PROPERTY_LIST_URL, {"baths": "8+"})
        self.assertEqual(len(response.data["results"]), 1)

        response = self.client.get(MY_LISTING_URL, {"beds": "8+"})
        self.assertEqual(len(response.data["results"]), 1)

        response = self.client.get(MY_LISTING_URL, {"baths": "8+"})
        self.assertEqual(len(response.data["results"]), 1)

    def test_filter_by_price_and_area_sqft_range(self):
        """Test RangeFilter for price."""
        self.dummy_properties()
        self._authenticate(self.agent_user)

        response = self.client.get(
            PROPERTY_LIST_URL, {"price_min": 2500, "price_max": 5500}
        )
        self.assertEqual(len(response.data["results"]), 3)

        response = self.client.get(
            PROPERTY_LIST_URL, {"area_sqft_min": 2500, "area_sqft_max": 5500}
        )
        self.assertEqual(len(response.data["results"]), 3)

        response = self.client.get(
            MY_LISTING_URL, {"price_min": 2500, "price_max": 5500}
        )
        self.assertEqual(len(response.data["results"]), 3)

        response = self.client.get(
            MY_LISTING_URL, {"area_sqft_min": 2500, "area_sqft_max": 5500}
        )
        self.assertEqual(len(response.data["results"]), 3)

    def test_search_filter(self):
        """Test the custom 'search' method filter."""
        self.dummy_properties()
        self._authenticate(self.agent_user)

        response = self.client.get(PROPERTY_LIST_URL, {"search": "Street 10"})
        self.assertEqual(len(response.data["results"]), 1)

        response = self.client.get(MY_LISTING_URL, {"search": "Street 10"})
        self.assertEqual(len(response.data["results"]), 1)
