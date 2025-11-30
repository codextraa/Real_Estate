# from rest_framework import status
# from rest_framework.test import APITestCase, APIClient
# from django.urls import reverse
# from django.contrib.auth import get_user_model
# from core_db.models import Property

# User = get_user_model()

# PROPERTY_LIST_URL = reverse("property-list")
# PROPERTY_DETAIL_URL = lambda pk: reverse("property-detail", kwargs={"pk": pk})


# class PropertyViewSetTests(APITestCase):
#     """Tests for the PropertyViewSet covering CRUD actions and permission control."""

#     def setUp(self):
#         self.password = "StrongP@ss123"
#         self.client = APIClient()

#         # 1. Test Users
#         self.superuser = User.objects.create_superuser(
#             email="super@test.com", username="superadmin", password=self.password
#         )

#         self.staff_user = User.objects.create_user(
#             email="staff@test.com",
#             username="staffuser",
#             password=self.password,
#             is_staff=True,
#         )

#         self.agent_owner = User.objects.create_user(
#             email="owner@test.com",
#             username="agentowner",
#             password=self.password,
#             is_agent=True,
#         )

#         self.agent_other = User.objects.create_user(
#             email="other@test.com",
#             username="agentother",
#             password=self.password,
#             is_agent=True,
#         )
#         self.normal_user = User.objects.create_user(
#             email="normal@test.com", username="normaluser", password=self.password
#         )

#         # 2. Test Properties
#         self.published_property = Property.objects.create(
#             title="Published House",
#             price=300000,
#             is_published=True,
#             agent=self.agent_owner,
#         )

#         self.draft_property = Property.objects.create(
#             title="Draft Apartment",
#             price=150000,
#             is_published=False,
#             agent=self.agent_owner,
#         )

#         self.other_agent_property = Property.objects.create(
#             title="Other Agent Listing",
#             price=500000,
#             is_published=True,
#             agent=self.agent_other,
#         )

#     def _authenticate(self, user):
#         """Helper to set authentication header for the client."""
#         self.client.force_authenticate(user=user)

#     def get_valid_create_data(self):
#         """Returns valid data for creating a new property."""
#         return {
#             "title": "New Listing for Sale",
#             "description": "A beautiful, modern property.",
#             "price": 450000,
#             "bedrooms": 3,
#             "agent": self.agent_owner.pk,  # Must include the agent ID
#         }

#     # --- LIST & RETRIEVE TESTS (GET) ---
#     # Testing visibility rules (published vs. draft, all vs. self-owned)
#     # ------------------------------------

#     def test_list_properties_unauthenticated_only_published(self):
#         """Unauthenticated users should only see published properties."""
#         response = self.client.get(PROPERTY_LIST_URL)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         # Expect 2 properties: self.published_property, self.other_agent_property
#         self.assertEqual(len(response.data), 2)
#         titles = [p["title"] for p in response.data]
#         self.assertIn("Published House", titles)
#         self.assertIn("Other Agent Listing", titles)
#         self.assertNotIn("Draft Apartment", titles)

#     def test_list_properties_normal_user_only_published(self):
#         """Normal authenticated users should only see published properties."""
#         self._authenticate(self.normal_user)
#         response = self.client.get(PROPERTY_LIST_URL)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(len(response.data), 2)

#     def test_list_properties_agent_owner_sees_all(self):
#         """Agent should see all properties (published/draft) they own and all other published properties."""
#         self._authenticate(self.agent_owner)
#         response = self.client.get(PROPERTY_LIST_URL)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         # Expect 3 properties: published, draft (owner's), other_agent_property (published)
#         self.assertEqual(len(response.data), 3)

#     def test_list_properties_superuser_sees_all(self):
#         """Superuser should see all properties (published/draft/all owners)."""
#         self._authenticate(self.superuser)
#         response = self.client.get(PROPERTY_LIST_URL)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         # Expect 3 properties in total
#         self.assertEqual(len(response.data), 3)

#     def test_retrieve_published_property_unauthenticated(self):
#         """Unauthenticated user can retrieve a published property."""
#         url = PROPERTY_DETAIL_URL(self.published_property.pk)
#         response = self.client.get(url)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(response.data["title"], "Published House")

#     def test_retrieve_draft_property_unauthenticated_denied(self):
#         """Unauthenticated user cannot retrieve a draft property."""
#         url = PROPERTY_DETAIL_URL(self.draft_property.pk)
#         response = self.client.get(url)
#         self.assertEqual(
#             response.status_code, status.HTTP_404_NOT_FOUND
#         )  # Filtered out by get_queryset

#     def test_retrieve_draft_property_by_owner_allowed(self):
#         """Agent owner can retrieve their own draft property."""
#         self._authenticate(self.agent_owner)
#         url = PROPERTY_DETAIL_URL(self.draft_property.pk)
#         response = self.client.get(url)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(response.data["title"], "Draft Apartment")

#     # --- CREATE TESTS (POST) ---
#     # Testing required authentication and required fields.
#     # ---------------------------

#     def test_create_property_unauthenticated_denied(self):
#         """Unauthenticated user cannot create a property."""
#         data = self.get_valid_create_data()
#         response = self.client.post(PROPERTY_LIST_URL, data, format="json")
#         self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
#         self.assertEqual(Property.objects.count(), 3)  # No new property created

#     def test_create_property_normal_user_denied(self):
#         """Normal user cannot create a property."""
#         self._authenticate(self.normal_user)
#         data = self.get_valid_create_data()
#         response = self.client.post(PROPERTY_LIST_URL, data, format="json")
#         # Assuming permissions are set to allow POST only for Staff/Agent
#         self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
#         self.assertEqual(Property.objects.count(), 3)

#     def test_create_property_agent_success(self):
#         """Agent can successfully create a property listing."""
#         self._authenticate(self.agent_owner)
#         data = self.get_valid_create_data()
#         response = self.client.post(PROPERTY_LIST_URL, data, format="json")

#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#         self.assertEqual(Property.objects.count(), 4)
#         new_property = Property.objects.get(pk=response.data["id"])
#         self.assertEqual(new_property.title, data["title"])
#         # Check that the agent field is automatically set/validated correctly
#         self.assertEqual(new_property.agent.pk, self.agent_owner.pk)

#     def test_create_property_missing_required_field(self):
#         """Test serializer validation for a missing required field (e.g., price)."""
#         self._authenticate(self.agent_owner)
#         data = self.get_valid_create_data()
#         del data["price"]  # Remove a required field
#         response = self.client.post(PROPERTY_LIST_URL, data, format="json")

#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         # Check for specific serializer error message
#         self.assertIn("price", response.data)
#         self.assertIn("This field is required.", response.data["price"])
#         self.assertEqual(Property.objects.count(), 3)

#     # --- UPDATE TESTS (PATCH) ---
#     # Testing who can update and what fields are allowed/required.
#     # ----------------------------

#     def test_update_property_owner_agent_success(self):
#         """Agent owner can successfully update their own property (e.g., change price)."""
#         self._authenticate(self.agent_owner)
#         url = PROPERTY_DETAIL_URL(self.published_property.pk)
#         new_price = 350000.00
#         patch_data = {"price": new_price}
#         response = self.client.patch(url, patch_data, format="json")

#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.published_property.refresh_from_db()
#         self.assertEqual(self.published_property.price, new_price)

#     def test_update_property_other_agent_denied(self):
#         """Agent cannot update a property owned by another agent."""
#         self._authenticate(
#             self.agent_owner
#         )  # Agent trying to update other agent's property
#         url = PROPERTY_DETAIL_URL(self.other_agent_property.pk)
#         old_price = self.other_agent_property.price
#         patch_data = {"price": 10.00}
#         response = self.client.patch(url, patch_data, format="json")

#         # Should be denied because of permission check on the object
#         self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
#         self.other_agent_property.refresh_from_db()
#         self.assertEqual(
#             self.other_agent_property.price, old_price
#         )  # Price should be unchanged

#     def test_update_property_superuser_can_update_any_property(self):
#         """Superuser can update any property, regardless of owner."""
#         self._authenticate(self.superuser)
#         url = PROPERTY_DETAIL_URL(self.other_agent_property.pk)
#         new_title = "Superuser Updated Title"
#         patch_data = {"title": new_title}
#         response = self.client.patch(url, patch_data, format="json")

#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.other_agent_property.refresh_from_db()
#         self.assertEqual(self.other_agent_property.title, new_title)

#     def test_update_property_with_invalid_data_type(self):
#         """Test serializer validation for invalid data (e.g., non-numeric price)."""
#         self._authenticate(self.agent_owner)
#         url = PROPERTY_DETAIL_URL(self.published_property.pk)
#         patch_data = {"price": "not_a_number"}
#         response = self.client.patch(url, patch_data, format="json")

#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertIn("price", response.data)
#         self.assertIn("A valid number is required", str(response.data["price"]))

#     # --- DELETE TESTS (DELETE) ---
#     # Testing who can delete.
#     # ---------------------------

#     def test_delete_property_owner_agent_success(self):
#         """Agent owner can delete their own property."""
#         self._authenticate(self.agent_owner)
#         url = PROPERTY_DETAIL_URL(self.published_property.pk)
#         response = self.client.delete(url)

#         self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
#         self.assertEqual(Property.objects.count(), 2)
#         self.assertFalse(
#             Property.objects.filter(pk=self.published_property.pk).exists()
#         )

#     def test_delete_property_other_agent_denied(self):
#         """Agent cannot delete another agent's property."""
#         self._authenticate(
#             self.agent_owner
#         )  # Agent owner trying to delete OTHER agent's property
#         url = PROPERTY_DETAIL_URL(self.other_agent_property.pk)
#         response = self.client.delete(url)

#         self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
#         self.assertEqual(Property.objects.count(), 3)
#         self.assertTrue(
#             Property.objects.filter(pk=self.other_agent_property.pk).exists()
#         )

#     def test_delete_property_normal_user_denied(self):
#         """Normal user cannot delete any property."""
#         self._authenticate(self.normal_user)
#         url = PROPERTY_DETAIL_URL(self.published_property.pk)
#         response = self.client.delete(url)

#         self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
#         self.assertEqual(Property.objects.count(), 3)
#         self.assertTrue(Property.objects.filter(pk=self.published_property.pk).exists())
