import io
import os
from PIL import Image
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from core_db.models import Agent

User = get_user_model()


class AgentImageValidationTests(APITestCase):
    """Tests for Image Validation (Size, Type) in both Create and Update for Agents."""

    def setUp(self):
        self.client = APIClient()
        self.password = "StrongP@ss123"

        self.agent_user = User.objects.create_user(
            email="existing@test.com",
            username="existinguser",
            password=self.password,
            is_agent=True,
        )
        self.agent_profile = Agent.objects.create(
            user=self.agent_user, company_name="Existing Realty"
        )

        self.detail_url = reverse("agent-detail", kwargs={"pk": self.agent_user.pk})

    def tearDown(self):
        """Cleanup files generated during tests."""
        self.agent_profile.refresh_from_db()
        if (
            self.agent_profile.image_url
            and "default" not in self.agent_profile.image_url.name
        ):
            if os.path.exists(self.agent_profile.image_url.path):
                os.remove(self.agent_profile.image_url.path)

    def _generate_test_image(self, name="test.jpg", format="JPEG", size=(100, 100)):
        """Helper to create a valid small image in memory."""
        image = Image.new("RGB", size, color="white")
        image_bytes = io.BytesIO()
        image.save(image_bytes, format=format)
        image_bytes.seek(0)
        return SimpleUploadedFile(
            name, image_bytes.read(), content_type=f"image/{format.lower()}"
        )

    def _generate_invalid_size_file(self, name="big.jpg"):
        """Creates a file larger than 2MB."""
        image = Image.new("RGB", (100, 100))
        image_bytes = io.BytesIO()
        image.save(image_bytes, format="JPEG")
        content = image_bytes.getvalue() + (b"0" * 3 * 1024 * 1024)  # 3MB
        return SimpleUploadedFile(name, content, content_type="image/jpeg")

    ### -------- TESTS --------

    def test_agent_can_upload_image_after_registration(self):
        """Test the 'Step 2' logic: Existing agent uploads a profile picture."""
        self.client.force_authenticate(user=self.agent_user)
        image = self._generate_test_image(name="profile_proc.jpg")

        response = self.client.patch(
            self.detail_url, {"profile_image": image}, format="multipart"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.agent_profile.refresh_from_db()
        self.assertIn("profile_proc", self.agent_profile.image_url.name)

    def test_agent_image_size_exceed_fails(self):
        """Verify 2MB limit during registration."""
        self.client.force_authenticate(user=self.agent_user)
        image = self._generate_invalid_size_file()

        response = self.client.patch(
            self.detail_url, {"profile_image": image}, format="multipart"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["image_url"]["size"], "Image size should not exceed 2MB."
        )

    def test_create_agent_image_type_invalid_fails(self):
        """Verify only JPEG/PNG allowed during registration (sending GIF)."""
        self.client.force_authenticate(user=self.agent_user)
        image = self._generate_test_image(format="GIF")

        response = self.client.patch(
            self.detail_url, {"profile_image": image}, format="multipart"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["image_url"]["type"], "Image type should be JPEG, PNG"
        )

    def test_create_agent_bad_request_invalid_file(self):
        """Test uploading a non-image file (text file)."""
        self.client.force_authenticate(user=self.agent_user)
        invalid_file = SimpleUploadedFile(
            "test.txt", b"not-an-image", content_type="text/plain"
        )

        response = self.client.patch(
            self.detail_url, {"profile_image": invalid_file}, format="multipart"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("image_url", response.data)

    def test_update_agent_image_formats_success(self):
        """Test that both JPEG and PNG formats are accepted for profile images."""
        self.client.force_authenticate(user=self.agent_user)

        formats = [("profile.jpg", "JPEG"), ("profile.png", "PNG")]

        for filename, fmt in formats:
            image = self._generate_test_image(name=filename, format=fmt)

            response = self.client.patch(
                self.detail_url, {"profile_image": image}, format="multipart"
            )

            self.assertEqual(
                response.status_code,
                status.HTTP_200_OK,
                f"Failed to upload {fmt} format.",
            )

            self.agent_profile.refresh_from_db()
            extension = filename.split(".")[-1].lower()
            self.assertTrue(
                self.agent_profile.image_url.name.lower().endswith(extension),
                f"Saved file extension does not match {extension}",
            )
