from django.test import TestCase
from django.contrib.auth import get_user_model
from core_db.models import Agent, Property
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError


class PropertyModelTest(TestCase):
    """Test Cases for the Property model."""

    def setUp(self):
        """Set up a required Agent instance and base property data."""

        self.user = get_user_model().objects.create_user(
            email="agent@example.com",
            password="Django@123",
        )

        self.base_data = {
            "user": self.user,
            "company_name": "Test Realty Group",
        }

        self.agent = Agent.objects.create(**self.base_data)

        self.property_info = {
            "agent": self.agent,
            "title": "Valid Test Listing",
            "description": "A nice description.",
            "beds": 2,
            "baths": 2,
            "price": 100000.50,
            "area_sqft": 850,
            "address": "456 Test Street",
        }

    def test_property_creation_success(self):
        """Test creating property is successful."""

        property = Property.objects.create(**self.property_info)

        self.assertEqual(property.agent, self.agent)
        self.assertEqual(property.title, "Valid Test Listing")
        self.assertEqual(property.description, "A nice description.")
        self.assertEqual(property.beds, 2)
        self.assertEqual(property.baths, 2)
        self.assertEqual(property.price, 100000.50)
        self.assertEqual(property.area_sqft, 850)
        self.assertEqual(property.address, "456 Test Street")

    def test_property_creation_requires_agent(self):
        """Test creating property without an agent."""

        data_no_agent = self.property_info.copy()
        data_no_agent.pop("agent")

        with self.assertRaises(ValidationError):
            Property.objects.create(**data_no_agent)

    def test_property_creation_without_title(self):
        """Test creating property without title."""

        data_no_title = self.property_info.copy()
        data_no_title.pop("title")
        with self.assertRaises(ValidationError):
            Property.objects.create(**data_no_title)

    def test_property_creation_without_description(self):
        """Test creating property without description."""
        data_no_description = self.property_info.copy()
        data_no_description.pop("description")
        with self.assertRaises(ValidationError):
            Property.objects.create(**data_no_description)

    def test_property_creation_without_beds(self):
        """Test creating property without beds."""
        data_no_beds = self.property_info.copy()
        data_no_beds.pop("beds")
        with self.assertRaises(ValidationError):
            Property.objects.create(**data_no_beds)

    def test_property_creation_without_baths(self):
        """Test creating property without baths."""
        data_no_baths = self.property_info.copy()
        data_no_baths.pop("baths")
        with self.assertRaises(ValidationError):
            Property.objects.create(**data_no_baths)

    def test_property_creation_without_price(self):
        """Test creating property without price."""
        data_no_price = self.property_info.copy()
        data_no_price.pop("price")
        with self.assertRaises(ValidationError):
            Property.objects.create(**data_no_price)

    def test_property_creation_without_area_sqft(self):
        """Test creating property without area_sqft."""
        data_no_area_sqft = self.property_info.copy()
        data_no_area_sqft.pop("area_sqft")
        with self.assertRaises(ValidationError):
            Property.objects.create(**data_no_area_sqft)

    def test_property_creation_without_address(self):
        """Test creating property without address."""
        data_no_address = self.property_info.copy()
        data_no_address.pop("address")
        with self.assertRaises(ValidationError):
            Property.objects.create(**data_no_address)

    def test_creating_property_with_title_length_more_than_150(self):
        """Test creating property with title length more than 150."""

        data_invalid = self.property_info.copy()
        data_invalid["title"] = "a" * 151

        with self.assertRaises(ValidationError):
            Property.objects.create(**data_invalid)

    def test_creating_property_bed_with_non_integer_value(self):
        """Test creating property with a non-integer value for beds."""
        data_invalid = self.property_info.copy()
        data_invalid["beds"] = "not_an_int"

        with self.assertRaises(ValidationError):
            Property.objects.create(**data_invalid)

    def test_creating_property_with_non_float_price_value_fails(self):
        """Test creating property with a non-float value for price raises ValueError/DataError."""
        data_invalid = self.property_info.copy()
        data_invalid["price"] = "not_a_number"

        with self.assertRaises(ValidationError):
            Property.objects.create(**data_invalid)

    def test_creating_property_with_non_integer_area_value_fails(self):
        """Test creating property with a non-integer value for area_sqft raises ValueError/DataError."""
        data_invalid = self.property_info.copy()
        data_invalid["area_sqft"] = "not_an_int"

        with self.assertRaises(ValidationError):
            Property.objects.create(**data_invalid)

    def test_creating_property_bath_with_non_integer_value(self):
        """Test creating property with a non-integer value for beds."""
        data_invalid = self.property_info.copy()
        data_invalid["baths"] = "not_an_int"

        with self.assertRaises(ValidationError):
            Property.objects.create(**data_invalid)

    def test_creating_property_with_address_length_more_than_255(self):
        """Test creating property with address length more than 255."""

        data_invalid = self.property_info.copy()
        data_invalid["address"] = "a" * 256

        with self.assertRaises(ValidationError):
            Property.objects.create(**data_invalid)

    def test_create_slug_from_title(self):
        """Test creating slug from title"""

        property = Property.objects.create(**self.property_info)

        self.assertEqual(property.slug, "valid-test-listing")

    def test_slug_is_updated(self):
        """Test slug is updated"""

        property = Property.objects.create(**self.property_info)
        title = "Exquisite Renovated Victorian Estate"
        property.title = title
        property.save()

        self.assertEqual(property.slug, "exquisite-renovated-victorian-estate")

    def test_check_slug_field_is_not_overridden(self):
        """Test creating slug from the given slug"""

        slug = "abcestate"
        property = Property.objects.create(**self.property_info, slug=slug)

        self.assertEqual(property.slug, "valid-test-listing")
