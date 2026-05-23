from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.core.cache import cache
from core_db_ai.models import AIReport
from report_api.tasks import (
    search_properties,
    compile_search_data,
    report_analysis,
    report_finalizer,
    parallel_report_generator,
)


class AIReportTasksTests(TestCase):

    def setUp(self):
        self.report_id = 1
        self.user_lock_key = "user_report_lock:1"
        self.property_data = {
            "title": "Test Property",
            "price": 500000,
            "area_sqft": 1500,
            "beds": 3,
            "baths": 2,
            "city": "Tech City",
            "area": "Silicon Valley",
        }
        # Mock the AIReport object
        self.mock_report = MagicMock(spec=AIReport)
        self.mock_report.id = self.report_id
        self.mock_report.status = "PROCESSING"

    def tearDown(self):
        cache.clear()

    ## --- 1. Search Properties Task ---

    @patch("report_api.tasks.generate_mock_properties")
    def test_search_properties_mock_call(self, mock_gen):
        """Test if search_properties calls the mock generator with correct data."""
        mock_gen.return_value = [{"price": 100}]

        result = search_properties(
            self.report_id, self.property_data, 25, 0, self.user_lock_key
        )

        mock_gen.assert_called_once_with(1500, 3, 2, 25)
        self.assertEqual(result, [{"price": 100}])

    ## --- 2. Compile Search Data Task ---

    @patch("report_api.tasks.clean_properties")
    def test_compile_search_data_deduplication(self, mock_clean):
        """Test merging and deduplication based on fingerprint."""
        # Mock clean_properties to return (price, sqft, beds, baths)
        mock_clean.side_effect = [
            (500000, 1500, 3, 2),  # Unique 1
            (500000, 1500, 3, 2),  # Duplicate of 1
            (600000, 1800, 4, 3),  # Unique 2
        ]

        results = [[{"item": 1}, {"item": 2}], [{"item": 3}]]  # Chunk 1  # Chunk 2

        final_list = compile_search_data(results, self.property_data)

        self.assertEqual(len(final_list), 2)
        self.assertEqual(final_list[0]["price"], 500000)
        self.assertEqual(final_list[1]["price"], 600000)

    ## --- 3. Report Analysis Task ---

    @patch("report_api.tasks.generate_mock_summary")
    def test_report_analysis_output_structure(self, mock_summary):
        """Verify the analysis returns the expected dictionary format."""
        mock_summary.return_value = "Mocked AI Summary Text"

        result = report_analysis([], self.report_id, self.property_data)

        self.assertEqual(result["investment_rating"], 0)
        self.assertIn("ai_insight_summary", result)
        self.assertEqual(result["ai_insight_summary"], "Mocked AI Summary Text")

    ## --- 4. Report Finalizer Task ---

    @patch("report_api.tasks.AIReport.objects.get")
    def test_report_finalizer_success(self, mock_get):
        """Test that finalizer updates DB fields correctly from analysis result."""
        mock_report = MagicMock()
        mock_get.return_value = mock_report

        analysis_result = {
            "avg_market_price": 450000,
            "investment_rating": 4.5,
            "ai_insight_summary": {
                "investment_summary": "Good buy",
                "weighted_analysis": "Scores look good",
                "pros": ["Cheap"],
                "cons": ["None"],
            },
        }

        report_finalizer(analysis_result, [], self.report_id, self.user_lock_key)

        # Verify status update
        self.assertEqual(mock_report.status, "COMPLETED")
        self.assertEqual(mock_report.investment_rating, 4.5)
        self.assertIn("PROS:", mock_report.ai_insight_summary)
        mock_report.save.assert_called()

    @patch("report_api.tasks.AIReport.objects.get")
    @patch("report_api.tasks.release_report_locks")
    def test_report_finalizer_failure_handling(self, mock_release, mock_get):
        """Test finalizer behavior when analysis_result contains a failure string."""
        mock_report = MagicMock()
        mock_get.return_value = mock_report

        # Simulating a failure result (non-dict ai_insight_summary)
        analysis_result = {"ai_insight_summary": "Search failed"}

        report_finalizer(analysis_result, [], self.report_id, self.user_lock_key)

        self.assertEqual(mock_report.status, "FAILED")
        mock_release.assert_called_once_with(self.user_lock_key)

    ## --- 5. Parallel Report Generator (Orchestration) ---

    @patch("report_api.tasks.AIReport.objects.filter")
    @patch("report_api.tasks.chord")
    def test_parallel_report_generator_workflow(self, mock_chord, mock_filter):
        """Test if the generator creates 4 search tasks and chains them into a chord."""
        mock_query = MagicMock()
        mock_query.exists.return_value = True
        mock_filter.return_value = mock_query

        # Mock the chord object and its calling chain
        chord_instance = mock_chord.return_value

        parallel_report_generator(
            self.report_id, self.property_data, self.user_lock_key
        )

        # Verify status update to PROCESSING
        mock_query.update.assert_called_with(status="PROCESSING")

        # Verify that 4 search tasks were added to the chord header
        header_tasks = mock_chord.call_args[0][0]
        self.assertEqual(len(header_tasks), 4)

        # Verify stagger (countdown) logic: 0*20, 1*20, 2*20, 3*20
        # Accessing task signatures (header_tasks)
        for i, task_sig in enumerate(header_tasks):
            self.assertEqual(task_sig.options["countdown"], i * 20)
