from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from decimal import Decimal
from core_db_ai.models import Agent, Property, AIReport

User = get_user_model()


class AIReportTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="password123",
            first_name="John",
            last_name="Doe",
            slug="john-doe",
        )

        self.agent = Agent.objects.create(
            user=self.user, company_name="Dream Realty", bio="Expert in urban lofts"
        )

        self.property = Property.objects.create(
            agent=self.agent,
            title="Modern Condo",
            description="A beautiful condo in the city center",
            beds=2,
            baths=2,
            price=500000.00,
            area_sqft=1200,
            address="123 Main St",
            slug="modern-condo",
        )

    def test_ai_report_creation(self):
        """Test that AIReport is created successfully."""
        report = AIReport.objects.create(
            property=self.property,
            user=self.user,
            status=AIReport.Status.PENDING,
            extracted_city="New York",
            investment_rating=4.5,
        )

        self.assertEqual(AIReport.objects.count(), 1)
        self.assertEqual(report.property.title, "Modern Condo")
        self.assertEqual(float(report.investment_rating), 4.5)
        self.assertEqual(report.status, "PENDING")

    def test_json_field_storage(self):
        """Test that comparable_data (JSON) stores correctly."""
        data = {"comp1": 450000, "comp2": 510000}
        report = AIReport.objects.create(
            property=self.property, user=self.user, comparable_data=data
        )

        report.refresh_from_db()
        self.assertEqual(report.comparable_data["comp1"], 450000)

    def test_investment_rating_limits(self):
        """Test that investment_rating is caught."""
        report = AIReport(property=self.property, user=self.user, investment_rating=5.1)

        with self.assertRaises(ValidationError):
            report.save()

        report = AIReport(
            property=self.property, user=self.user, investment_rating=-0.1
        )

        with self.assertRaises(ValidationError):
            report.save()

    def test_invalid_status_choice(self):
        """Test that invalid status triggers ValidationError on save."""
        report = AIReport(
            property=self.property, user=self.user, status="INVALID_STATUS"
        )

        with self.assertRaises(ValidationError):
            report.save()

    def test_decimal_max_digits_validation(self):
        """Test that max_digits is respected."""
        too_large_value = Decimal("10000000000000.00")

        report = AIReport(
            property=self.property, user=self.user, avg_market_price=too_large_value
        )

        with self.assertRaises(ValidationError):
            report.save()

        report = AIReport(
            property=self.property, user=self.user, avg_price_per_sqft=too_large_value
        )

        with self.assertRaises(ValidationError):
            report.save()

    def test_precision_rounding(self):
        """Test that it handles decimal places correctly."""
        report = AIReport(
            property=self.property, user=self.user, investment_rating=Decimal("4.55")
        )

        with self.assertRaises(ValidationError):
            report.save()

    def test_property_cascade_only(self):
        """Test that deleting a Property deletes its AIReports but keeps the Agent."""
        AIReport.objects.create(property=self.property, user=self.user)

        self.property.delete()

        self.assertTrue(Agent.objects.filter(id=self.agent.id).exists())
        self.assertEqual(AIReport.objects.count(), 0)
