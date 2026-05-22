from unittest.mock import patch, MagicMock
from django.test import TestCase
from celery.exceptions import MaxRetriesExceededError
from core_db_ai.models import ChatMessage, AIReport
from chat_api.tasks import (
    ai_message_extractor,
    ai_message_analysis,
    finalizer_task,
    generate_ai_chat_response
)

class ChatMessageTasksTests(TestCase):

    def setUp(self):
        self.session_id = 1
        self.message_id = 50
        self.user_lock_key = "user_chat_lock:1"
        self.user_query = "What if the price was $250,000?"

    ## --- 1. AI MESSAGE EXTRACTOR ---
    @patch("chat_api.tasks.ChatMessage.objects.get")
    @patch("chat_api.tasks.ChatSession.objects.get")
    def test_ai_message_extractor_stops_chain(self, mock_get_session, mock_get_message):
        mock_msg = MagicMock()
        mock_get_message.return_value = mock_msg
        mock_sess = MagicMock()
        mock_sess.user_message_count = 0
        mock_get_session.return_value = mock_sess

        # DO NOT pass None or self here. Celery injects it automatically into .run()
        result = ai_message_extractor.run(
            session_id=self.session_id,
            message_id=self.message_id,
            property_details={"title": "Test"},
            user_query=self.user_query,
            user_lock_key=self.user_lock_key
        )
        self.assertEqual(result, "Stopped")

    ## --- 2. AI MESSAGE ANALYSIS ---
    @patch("chat_api.tasks.InvestmentRegressor.calculate_rating")
    @patch("chat_api.tasks.groq_ai_insight_prompt")
    @patch("chat_api.tasks.ChatMessage.objects.get")
    def test_ai_message_analysis_success(self, mock_get_message, mock_groq, mock_regress):
        mock_regress.return_value = (4.0, {"logic": "good"})
        mock_groq.return_value = ({"investment_summary": "Buy"}, MagicMock())

        report_details = {
            "comparable_data": [], 
            "avg_market_price": "300000", 
            "avg_price_per_sqft": "200", 
            "avg_beds": "3", 
            "avg_baths": "2"
        }
        
        # Again, start directly with property_json. Celery handles 'self'.
        result = ai_message_analysis.run(
            property_json={"price": 250000},
            message_id=self.message_id,
            report_details=report_details,
            user_query=self.user_query,
            user_lock_key=self.user_lock_key
        )
        self.assertEqual(result["rating"], 4.0)

    @patch("chat_api.tasks.ai_message_analysis.retry")
    @patch("chat_api.tasks.ChatMessage.objects.get")
    @patch("chat_api.tasks.release_chat_locks")
    def test_ai_message_analysis_max_retries_failure(self, mock_release, mock_get_message, mock_retry):
        mock_msg = MagicMock()
        mock_get_message.return_value = mock_msg
        mock_retry.side_effect = MaxRetriesExceededError()
        
        report_details = {
            "avg_market_price": 10, "avg_price_per_sqft": 10, 
            "avg_beds": 1, "avg_baths": 1, "comparable_data": []
        }

        with patch("chat_api.tasks.groq_ai_insight_prompt", side_effect=Exception("API Down")):
            # If you need to mock self properties (like retries), 
            # you must patch 'chat_api.tasks.ai_message_analysis.request' instead of passing a mock.
            with patch('chat_api.tasks.ai_message_analysis.request') as mock_request:
                mock_request.retries = 3
                ai_message_analysis.max_retries = 3
                
                result = ai_message_analysis.run(
                    property_json={},
                    message_id=self.message_id,
                    report_details=report_details,
                    user_query=self.user_query,
                    user_lock_key=self.user_lock_key
                )

        self.assertEqual(result, "Stopped")
        mock_release.assert_called_once_with(self.user_lock_key)

    ## --- 3. FINALIZER TASK TESTS ---
    @patch("chat_api.tasks.ChatMessage.objects.get")
    @patch("chat_api.tasks.ChatSession.objects.get")
    def test_finalizer_task_success(self, mock_get_session, mock_get_message):
        mock_msg = MagicMock()
        mock_get_message.return_value = mock_msg
        mock_sess = MagicMock()
        mock_sess.user_message_count = 5
        mock_get_session.return_value = mock_sess

        analysis_result = {
            "rating": 4.2,
            "text": {
                "investment_summary": "Undervalued",
                "weighted_analysis": "Good",
                "pros": ["Low price"],
                "cons": ["Old roof"]
            }
        }

        # NOTE: finalizer_task is NOT bound, so NO 'self' or 'None' as 1st arg.
        # finalizer_task(analysis_result, session_id, message_id, user_lock_key)
        result = finalizer_task(
            analysis_result, self.session_id, self.message_id, self.user_lock_key
        )

        self.assertEqual(result, f"Message {self.message_id} Success")
        self.assertEqual(mock_msg.status, ChatMessage.Status.COMPLETED)
        self.assertIn("New Projected Rating: 4.2 / 5", mock_msg.content)
        self.assertEqual(mock_sess.user_message_count, 6)

    def test_finalizer_aborted_signal(self):
        result = finalizer_task("Stopped", self.session_id, self.message_id, self.user_lock_key)
        self.assertEqual(result, "Aborted")

    @patch("chat_api.tasks.ChatMessage.objects.get", side_effect=Exception("DB Error"))
    @patch("chat_api.tasks.ChatMessage.objects.filter")
    @patch("chat_api.tasks.release_chat_locks")
    def test_finalizer_exception_handling(self, mock_release, mock_filter, mock_get):
        mock_update_query = MagicMock()
        mock_filter.return_value = mock_update_query

        result = finalizer_task({"data": "dummy"}, self.session_id, self.message_id, self.user_lock_key)

        self.assertEqual(result, f"Message {self.message_id} Failed")
        mock_update_query.update.assert_called_once()
        mock_release.assert_called_once_with(self.user_lock_key)

    ## --- 4. ORCHESTRATOR ---
    @patch("chat_api.tasks.AIReport.objects.select_related")
    @patch("chat_api.tasks.ChatMessage.objects.get")
    @patch("chat_api.tasks.chain") 
    def test_generate_ai_chat_response_full_logic(self, mock_chain, mock_get_message, mock_report_select):
        mock_report = MagicMock(spec=AIReport)
        mock_report.id = 100
        mock_report.comparable_data = [{"price": 500000}]
        mock_report.avg_market_price = 450000
        mock_report.avg_price_per_sqft = 300
        mock_report.avg_beds = 3
        mock_report.avg_baths = 2
        mock_report.investment_rating = 4.0
        
        mock_property = MagicMock()
        mock_property.title = "Luxury Condo"
        mock_property.price = 480000
        mock_report.property = mock_property

        mock_report_select.return_value.get.return_value = mock_report
        mock_msg = MagicMock(spec=ChatMessage)
        mock_get_message.return_value = mock_msg

        generate_ai_chat_response(
            self.session_id, self.message_id, 100, self.user_query, self.user_lock_key
        )

        self.assertEqual(mock_msg.status, ChatMessage.Status.PROCESSING)
        mock_chain.assert_called_once()
        chain_args = mock_chain.call_args[0]
        self.assertEqual(len(chain_args), 3)