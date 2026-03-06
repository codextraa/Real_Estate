import io
from PIL import Image
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from core_db.models import Agent, Property

User = get_user_model()

class PropertyImageTests(APITestCase):
    """Tests for the image upload functionality of Properties."""

    def setUp(self):
        self.client = APIClient()
        self.password = "StrongP@ss123"

        # Setup Agent
        self.agent_user = User.objects.create_user(
            email="agent@test.com",
            username="agentuser",
            password=self.password,
            is_agent=True,
        )
        self.agent_profile = Agent.objects.create(
            user=self.agent_user, company_name="Test Realty"
        )

        # Setup Other Agent
        self.other_agent_user = User.objects.create_user(
            email="other@test.com",
            username="otheragent",
            password=self.password,
            is_agent=True,
        )
        self.other_agent_profile = Agent.objects.create(
            user=self.other_agent_user, company_name="Other Realty"
        )

        self.property = Property.objects.create(
            agent=self.agent_profile,
            title="Main Property",
            beds=2,
            baths=2,
            price=100000,
            area_sqft=1000,
            address="123 Image St"
        )

        # Initial payload
        self.payload = {
            "title": "New Property",
            "description": "A test property",
            "beds": 2,
            "baths": 2,
            "price": 100000,
            "area_sqft": 1000,
            "address": "123 Image St",
        }

        # URLs
        self.list_url = reverse("property-list")
        self.detail_url = reverse("property-detail", kwargs={"pk": self.property.pk})

    def tearDown(self):
        """Cleanup files generated during tests."""
        self.property.refresh_from_db()
        if self.property.image_url and "default" not in self.property.image_url.name:
            self.property.image_url.delete(save=False)

    def _authenticate(self, user):
        self.client.force_authenticate(user=user)

    def _generate_test_image(self, name="test.jpg", size=(100, 100), color="white", format="JPEG"):
        """Helper to create a real image file in memory."""
        image = Image.new("RGB", size, color)
        image_bytes = io.BytesIO()
        image.save(image_bytes, format=format)
        image_bytes.seek(0)
        return SimpleUploadedFile(
            name,
            content=image_bytes.read(),
            content_type=f"image/{format.lower()}"
        )

    ### -------- CREATE TEST --------

    def test_upload_image_to_create_property_success(self):
        """Test uploading an image to a property by the owner."""
        self._authenticate(self.agent_user)
        image = self._generate_test_image()
        self.payload["property_image"] = image
        
        response = self.client.post(self.list_url, self.payload, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        property_obj = Property.objects.get(title="New Property")
        self.assertIn("test", property_obj.image_url.name)
        self.assertTrue(property_obj.image_url.name.startswith('property_images/'))


    def test_upload_image_bad_request(self):
        """Test uploading an invalid image."""
        self._authenticate(self.agent_user)

        response = self.client.post(self.list_url, {}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        invalid_file = SimpleUploadedFile("test.txt", b"not-an-image", content_type="text/plain")
        bad_payload = self.payload.copy()
        bad_payload["property_image"] = invalid_file
        
        response = self.client.post(self.list_url, bad_payload, format="multipart")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("image_url", response.data)

    def test_upload_image_size_limit(self):
        """Test that image size exceeding 2MB is rejected."""
        self._authenticate(self.agent_user)
        image = Image.new("RGB", (100, 100)) # Small dimensions
        image_bytes = io.BytesIO()
        image.save(image_bytes, format="JPEG")
        large_content = image_bytes.getvalue() + (b"0" * 3 * 1024 * 1024)
        
        large_file = SimpleUploadedFile(
            "large.jpg", 
            large_content, 
            content_type="image/jpeg"
        )
        
        payload = self.payload.copy()
        payload["property_image"] = large_file
        
        response = self.client.post(self.list_url, payload, format="multipart")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("image_url", response.data)
        self.assertEqual(
            response.data["image_url"]["size"], 
            "Property image size should not exceed 2MB."
        )

    def test_upload_unsupported_image_type_fails(self):
        """Test that unsupported image formats (like GIF) are rejected."""
        self._authenticate(self.agent_user)
        
        url = self.list_url

        gif_image = self._generate_test_image(
            name="test.gif", 
            format="GIF"
        )
        
        payload = self.payload.copy()
        payload["property_image"] = gif_image
        
        response = self.client.post(url, payload, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        self.assertIn("image_url", response.data)
        self.assertIn("type", response.data["image_url"])
        self.assertEqual(
            response.data["image_url"]["type"], 
            "Property image type should be JPEG, PNG"
        )

    def test_upload_different_valid_formats(self):
        """Test that both PNG and JPEG are accepted specifically."""
        self._authenticate(self.agent_user)
        
        url = self.list_url
        formats = [("image.png", "PNG"), ("image.jpg", "JPEG")]

        for name, fmt in formats:
            image = self._generate_test_image(name=name, format=fmt)
            
            payload = self.payload.copy()
            payload["title"] = f"Format Test {name}" 
            payload["property_image"] = image
            
            response = self.client.post(url, payload, format="multipart")
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

            property_obj = Property.objects.filter(agent=self.agent_profile).latest('id')
            
            extension = name.split('.')[-1].lower() 
            self.assertIn(extension, property_obj.image_url.name.lower())



    ### -------- UPDATE TESTS --------

    def test_update_property_image_success(self):
            """Test successfully updating an image for an existing property."""
            self._authenticate(self.agent_user)
            
            new_image = self._generate_test_image(name="updated_image.png", format="PNG")
            
            response = self.client.patch(
                self.detail_url, 
                {"property_image": new_image}, 
                format="multipart"
            )
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            self.property.refresh_from_db()
            self.assertIn("updated_image", self.property.image_url.name)
            self.assertTrue(self.property.image_url.name.endswith('.png'))

    def test_update_image_size_limit_fails(self):
            """Test that updating with a >2MB image is rejected."""
            self._authenticate(self.agent_user)
            
            image = Image.new("RGB", (100, 100))
            image_bytes = io.BytesIO()
            image.save(image_bytes, format="JPEG")
            large_content = image_bytes.getvalue() + (b"0" * 3 * 1024 * 1024)
            
            large_file = SimpleUploadedFile(
                "too_big.jpg", 
                large_content, 
                content_type="image/jpeg"
            )
            
            response = self.client.patch(
                self.detail_url, 
                {"property_image": large_file}, 
                format="multipart"
            )
            
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn("image_url", response.data)
            self.assertEqual(
                response.data["image_url"]["size"], 
                "Property image size should not exceed 2MB."
            )

    def test_update_unsupported_image_type_fails(self):
        """Test that updating with a GIF is rejected."""
        self._authenticate(self.agent_user)
        
        gif_image = self._generate_test_image(name="test.gif", format="GIF")
        
        response = self.client.patch(
            self.detail_url, 
            {"property_image": gif_image}, 
            format="multipart"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("image_url", response.data)
        self.assertEqual(
            response.data["image_url"]["type"], 
            "Property image type should be JPEG, PNG"
        )

    def test_update_upload_different_valid_formats(self):
        """Test that both PNG and JPEG are accepted specifically."""
        self._authenticate(self.agent_user)
        
        url = self.detail_url
        formats = [("image.png", "PNG"), ("image.jpg", "JPEG")]

        for name, fmt in formats:
            image = self._generate_test_image(name=name, format=fmt)
            
            payload = self.payload.copy()
            payload["title"] = f"Format Test {name}" 
            payload["property_image"] = image
            
            response = self.client.patch(url, payload, format="multipart")
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            property_obj = Property.objects.filter(agent=self.agent_profile).latest('id')
            
            extension = name.split('.')[-1].lower() 
            self.assertIn(extension, property_obj.image_url.name.lower())

    def test_upload_image_bad_request_update(self):
        """Test uploading an invalid image for an existing property."""
        self._authenticate(self.agent_user)

        invalid_file = SimpleUploadedFile("test.txt", b"not-an-image", content_type="text/plain")
        bad_payload = self.payload.copy()
        bad_payload["property_image"] = invalid_file
        
        response = self.client.patch(self.detail_url, bad_payload, format="multipart")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("image_url", response.data)


