from unittest.mock import patch, MagicMock
from django.test import TestCase
from core_db_ai.models import AIReport, Property, User, Agent
from report_api.tasks import (
    search_properties,
    compile_search_data,
    report_finalizer,
    parallel_report_generator,
)


class AIReportTaskTests(TestCase):
    def setUp(self):
        # Setup basic data
        self.user = User.objects.create_user(
            email="t@t.com", username="t", password="p"
        )
        self.agent = Agent.objects.create(user=self.user, company_name="Test")
        self.property = Property.objects.create(
            agent=self.agent, title="Prop", price=100, area_sqft=10, beds=1, baths=1
        )
        self.report = AIReport.objects.create(user=self.user, property=self.property)
        self.property_data = {"area_sqft": 10, "beds": 1, "baths": 1}
        self.lock_key = "user_lock_1"

    # --- 1. Atomic Task Tests ---

    def test_search_properties_returns_mock_data(self):
        """Test that search_properties returns a list of items."""
        results = search_properties(
            self.report.id, self.property_data, 5, 0, self.lock_key
        )
        self.assertIsInstance(results, list)
        self.assertTrue(len(results) > 0)

    def test_compile_search_data_deduplication(self):
        """Test that compile_search_data removes duplicate properties using fingerprints."""
        # result is a list of results from parallel workers
        mock_results = [
            [{"price": 500, "area_sqft": 1000, "beds": 2, "baths": 2}],  # Worker 1
            [
                {"price": 500, "area_sqft": 1000, "beds": 2, "baths": 2}
            ],  # Worker 2 (Duplicate)
            [
                {"price": 600, "area_sqft": 1100, "beds": 3, "baths": 2}
            ],  # Worker 3 (Unique)
        ]

        # We need to mock 'clean_properties' because it's used inside
        with patch("report_api.tasks.clean_properties") as mock_clean:
            # Setup mock returns for cleaning
            mock_clean.side_effect = [
                (500, 1000, 2, 2),
                (500, 1000, 2, 2),
                (600, 1100, 3, 2),
            ]

            compiled = compile_search_data(mock_results, self.property_data)

            # Should have 2 unique items, not 3
            self.assertEqual(len(compiled), 2)
            self.assertEqual(compiled[0]["price"], 500)
            self.assertEqual(compiled[1]["price"], 600)

    def test_report_finalizer_success(self):
        """Test that the finalizer updates the database correctly."""
        analysis_result = {
            "avg_market_price": 550000,
            "investment_rating": 4.5,
            "ai_insight_summary": {
                "investment_summary": "Great deal",
                "weighted_analysis": "High growth",
                "pros": ["Cheap"],
                "cons": ["Small"],
            },
        }
        compiled_data = [{"price": 550000}]

        report_finalizer(analysis_result, compiled_data, self.report.id, self.lock_key)

        self.report.refresh_from_db()
        self.assertEqual(self.report.status, AIReport.Status.COMPLETED)
        self.assertEqual(float(self.report.avg_market_price), 550000.0)
        self.assertIn("PROS:\n- Cheap", self.report.ai_insight_summary)

    # --- 2. Workflow / Orchestration Tests ---

    @patch("core_db_ai.tasks.chord")
    def test_parallel_report_generator_logic(self, mock_chord):
        """Test the master task triggers processing status and calls chord."""
        # 1. Test status update
        parallel_report_generator(self.report.id, self.property_data, self.lock_key)

        self.report.refresh_from_db()
        self.assertEqual(self.report.status, AIReport.Status.PROCESSING)

        # 2. Test chord structure
        self.assertTrue(mock_chord.called)
        # Check that it generated 4 search tasks (as per your range(4))
        search_tasks_list = mock_chord.call_args[0][0]
        self.assertEqual(len(search_tasks_list), 4)

    def test_parallel_report_generator_non_existent_report(self):
        """Test that task returns None safely if report ID is invalid."""
        result = parallel_report_generator(9999, self.property_data, self.lock_key)
        self.assertIsNone(result)
