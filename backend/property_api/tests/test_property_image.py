import io, os
from PIL import Image
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from core_db.models import Agent, Property
from django.conf import settings

User = get_user_model()

PROPERTY_LIST_URL = reverse("property-list")
PROPERTY_DETAIL_URL = lambda pk: reverse("property-detail", kwargs={"pk": pk})


class PropertyImageTests(APITestCase):
    """Test suite for Property Image uploads and validation."""

    def setUp(self):
        self.client = APIClient()
        self.agent_user = User.objects.create_user(
            email="agent@test.com",
            username="agentuser",
            password="StrongP@ss123",
            is_agent=True,
        )
        self.agent_profile = Agent.objects.create(
            user=self.agent_user, company_name="Image Realty"
        )
        self._authenticate(self.agent_user)

    def _authenticate(self, user):
        """Helper to authenticate users."""
        self.client.force_authenticate(user=user)

    def generate_test_image(
        self, name="test.jpg", size=(100, 100), color="blue", format="JPEG"
    ):
        """Helper to create a valid image file in memory."""
        file_obj = io.BytesIO()
        image = Image.new("RGB", size, color=color)
        image.save(file_obj, format=format)
        file_obj.seek(0)
        return SimpleUploadedFile(
            name, file_obj.read(), content_type=f"image/{format.lower()}"
        )

    def get_valid_payload(self):
        return {
            "title": "Image Test Property",
            "description": "Testing uploads",
            "beds": 2,
            "baths": 2,
            "price": 300000,
            "area_sqft": 1500,
            "address": "123 Image St",
        }

    # def test_create_property_missing_image_fails(self):
    #     """Test that if 'property_image' is empty, validation fails."""
    #     payload = self.get_valid_payload()
    #     # Explicitly send empty value to trigger your serializer's 'if not value'
    #     payload["property_image"] = ""

    #     response = self.client.post(PROPERTY_LIST_URL, payload, format='multipart')

    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     # Note: DRF wraps simple ValidationErrors in a list [0]
    #     self.assertEqual(str(response.data["image_url"][0]), "Property image is required.")

    def test_create_property_with_image_success(self):
        """Test that an agent can successfully upload an image during property creation."""
        payload = self.get_valid_payload()
        payload["property_image"] = self.generate_test_image()

        response = self.client.post(PROPERTY_LIST_URL, payload, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        prop = Property.objects.get(address=payload["address"])
        self.assertTrue(
            prop.image_url and prop.image_url != "property_images/default_image.jpg"
        )

    def test_create_property_without_image_uses_default(self):
        """Test that the default image is assigned if no image is provided."""
        payload = self.get_valid_payload()

        response = self.client.post(PROPERTY_LIST_URL, payload, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        prop = Property.objects.get(address=payload["address"])
        self.assertEqual(prop.image_url, "property_images/default_image.jpg")

    # --- Validation---

    def test_image_invalid_type_fails(self):
        """Test that uploading a .txt file disguised as an image fails."""
        payload = self.get_valid_payload()
        payload["property_image"] = SimpleUploadedFile(
            "test.txt", b"not-an-image", content_type="text/plain"
        )

        response = self.client.post(PROPERTY_LIST_URL, payload, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("image_url", response.data)

    def test_image_too_large_fails(self):
        """Test that an image exceeding 2MB is rejected."""
        payload = self.get_valid_payload()

        file_obj = io.BytesIO()
        image = Image.new("RGB", (100, 100), color="red")
        image.save(file_obj, format="JPEG")

        large_content = file_obj.getvalue() + (b"0" * (2 * 1024 * 1024 + 1024))

        payload["property_image"] = SimpleUploadedFile(
            "large.jpg", large_content, content_type="image/jpeg"
        )

        response = self.client.post(PROPERTY_LIST_URL, payload, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        error_msg = response.data["image_url"]["size"]
        self.assertEqual(str(error_msg), "Property image size should not exceed 2MB.")

    def test_image_wrong_format_fails(self):
        """Test that only JPEG and PNG are allowed."""
        payload = self.get_valid_payload()
        payload["property_image"] = self.generate_test_image(
            name="test.gif", format="GIF"
        )

        response = self.client.post(PROPERTY_LIST_URL, payload, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        error_msg = response.data["image_url"]["type"]
        self.assertEqual(str(error_msg), "Property image type should be JPEG, PNG")

    ### --- Update ---

    def test_update_image_invalid_type_fails(self):
        """Test that updating with a .txt file disguised as an image fails."""
        payload = self.get_valid_payload()
        self.client.post(PROPERTY_LIST_URL, payload, format="multipart")
        prop = Property.objects.get(address=payload["address"])

        invalid_image = SimpleUploadedFile(
            "test.txt", b"not-an-image", content_type="text/plain"
        )
        url = PROPERTY_DETAIL_URL(prop.id)
        response = self.client.patch(
            url, {"property_image": invalid_image}, format="multipart"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("image_url", response.data)

    def test_update_image_too_large_fails(self):
        """Test that updating with an image exceeding 2MB is rejected."""
        payload = self.get_valid_payload()
        self.client.post(PROPERTY_LIST_URL, payload, format="multipart")
        prop = Property.objects.get(address=payload["address"])

        file_obj = io.BytesIO()
        image = Image.new("RGB", (100, 100), color="red")
        image.save(file_obj, format="JPEG")
        large_content = file_obj.getvalue() + (b"0" * (2 * 1024 * 1024 + 1024))
        large_image = SimpleUploadedFile(
            "large.jpg", large_content, content_type="image/jpeg"
        )

        url = PROPERTY_DETAIL_URL(prop.id)
        response = self.client.patch(
            url, {"property_image": large_image}, format="multipart"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_msg = response.data["image_url"]["size"]
        self.assertEqual(str(error_msg), "Property image size should not exceed 2MB.")

    def test_update_image_wrong_format_fails(self):
        """Test that updating with disallowed formats (e.g., GIF) fails."""
        payload = self.get_valid_payload()
        self.client.post(PROPERTY_LIST_URL, payload, format="multipart")
        prop = Property.objects.get(address=payload["address"])

        gif_image = self.generate_test_image(name="test.gif", format="GIF")
        url = PROPERTY_DETAIL_URL(prop.id)
        response = self.client.patch(
            url, {"property_image": gif_image}, format="multipart"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_msg = response.data["image_url"]["type"]
        self.assertEqual(str(error_msg), "Property image type should be JPEG, PNG")

    def test_update_property_image_replaces_and_deletes_old_file(self):
        """Test that updating an image deletes the old physical file from storage."""

        payload = self.get_valid_payload()
        initial_image_name = "initial_image.jpg"
        payload["property_image"] = self.generate_test_image(name=initial_image_name)

        self.client.post(PROPERTY_LIST_URL, payload, format="multipart")
        prop = Property.objects.get(address=payload["address"])
        old_image_path = os.path.join(settings.MEDIA_ROOT, prop.image_url.name)
        self.assertTrue(os.path.exists(old_image_path))

        new_image_name = "new_updated_image.jpg"
        new_image = self.generate_test_image(name=new_image_name)
        url = PROPERTY_DETAIL_URL(prop.id)

        response = self.client.patch(
            url, {"property_image": new_image}, format="multipart"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        prop.refresh_from_db()

        self.assertIn(new_image_name.split(".")[0], prop.image_url.name)
        self.assertFalse(
            os.path.exists(old_image_path),
            "Old image file was not deleted from storage.",
        )

    def test_update_property_image_does_not_delete_default(self):
        """Test that replacing a default image does NOT delete the default file."""

        payload = self.get_valid_payload()
        self.client.post(PROPERTY_LIST_URL, payload, format="multipart")
        prop = Property.objects.get(address=payload["address"])

        default_rel_path = "property_images/default_image.jpg"
        default_full_path = os.path.join(settings.MEDIA_ROOT, default_rel_path)
        os.makedirs(os.path.dirname(default_full_path), exist_ok=True)
        with open(default_full_path, "w") as f:
            f.write("default content")

        url = PROPERTY_DETAIL_URL(prop.id)
        new_image = self.generate_test_image(name="new_custom.jpg")
        response = self.client.patch(
            url, {"property_image": new_image}, format="multipart"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            os.path.exists(default_full_path),
            "Default image file was accidentally deleted.",
        )

    def test_partial_update_text_only_preserves_image(self):
        """Test that updating just a text field doesn't clear the existing image."""
        payload = self.get_valid_payload()
        payload["property_image"] = self.generate_test_image(name="keep_me.jpg")
        self.client.post(PROPERTY_LIST_URL, payload, format="multipart")

        prop = Property.objects.get(address=payload["address"])
        original_image_name = prop.image_url.name

        url = PROPERTY_DETAIL_URL(prop.id)
        response = self.client.patch(url, {"price": 999999}, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        prop.refresh_from_db()
        self.assertEqual(
            prop.image_url.name,
            original_image_name,
            "Image was changed during a text-only update.",
        )

    def test_unauthorized_agent_cannot_update_property_image(self):
        """Test that an agent cannot update or replace an image for another agent's property."""
        payload = self.get_valid_payload()
        payload["property_image"] = self.generate_test_image(
            name="agent_a_property.jpg"
        )
        self.client.post(PROPERTY_LIST_URL, payload, format="multipart")

        prop = Property.objects.get(address=payload["address"])
        original_image_path = os.path.join(settings.MEDIA_ROOT, prop.image_url.name)

        other_agent_user = User.objects.create_user(
            email="malicious_agent@test.com",
            username="malicious_agent",
            password="StrongP@ss123",
            is_agent=True,
        )
        Agent.objects.create(
            user=other_agent_user, company_name="Bad Intentions Realty"
        )

        self._authenticate(other_agent_user)

        url = PROPERTY_DETAIL_URL(prop.id)
        new_image = self.generate_test_image(name="attacker_image.jpg")
        response = self.client.patch(
            url, {"property_image": new_image}, format="multipart"
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        prop.refresh_from_db()
        self.assertIn("agent_a_property", prop.image_url.name)

        self.assertTrue(
            os.path.exists(original_image_path),
            "Original file was deleted by an unauthorized user!",
        )

    #### ---Delete---

    def test_delete_property_removes_image_file(self):
        """Test that deleting a property also removes its image."""
        payload = self.get_valid_payload()
        payload["property_image"] = self.generate_test_image(name="to_delete.jpg")

        create_res = self.client.post(
            reverse("property-list"), payload, format="multipart"
        )
        self.assertEqual(create_res.status_code, status.HTTP_201_CREATED)

        property_obj = Property.objects.get(address=payload["address"])
        property_id = property_obj.id

        image_path = os.path.join(settings.MEDIA_ROOT, property_obj.image_url.name)

        response = self.client.delete(
            reverse("property-detail", kwargs={"pk": property_id})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(os.path.exists(image_path))

    def test_delete_property_does_not_remove_default_image(self):
        """Test that deleting a property with a default image does NOT delete the file."""
        payload = self.get_valid_payload()
        payload["property_image"] = self.generate_test_image()

        create_res = self.client.post(
            reverse("property-list"), payload, format="multipart"
        )
        self.assertEqual(create_res.status_code, status.HTTP_201_CREATED)

        property_obj = Property.objects.get(address=payload["address"])
        property_id = property_obj.id

        default_rel_path = "property_images/default_image.jpg"
        property_obj.image_url = default_rel_path
        property_obj.save()

        default_full_path = os.path.join(settings.MEDIA_ROOT, default_rel_path)
        os.makedirs(os.path.dirname(default_full_path), exist_ok=True)
        if not os.path.exists(default_full_path):
            with open(default_full_path, "w") as f:
                f.write("default")

        self.client.delete(reverse("property-detail", kwargs={"pk": property_id}))
        self.assertTrue(os.path.exists(default_full_path))

    def test_unauthorized_agent_cannot_delete_property_or_image(self):
        """Test that an unauthorized agent cannot delete a property or trigger image removal."""
        payload = self.get_valid_payload()
        payload["property_image"] = self.generate_test_image(name="safe_file.jpg")
        self.client.post(reverse("property-list"), payload, format="multipart")
        prop = Property.objects.get(address=payload["address"])
        image_path = os.path.join(settings.MEDIA_ROOT, prop.image_url.name)

        other_user = User.objects.create_user(
            email="stranger@test.com",
            username="stranger",
            password="StrongP@ss123",
            is_agent=True,
        )
        Agent.objects.create(user=other_user, company_name="Other Co")
        self._authenticate(other_user)

        response = self.client.delete(
            reverse("property-detail", kwargs={"pk": prop.id})
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(
            os.path.exists(image_path),
            "Unauthorized deletion attempt must not remove the image file.",
        )
