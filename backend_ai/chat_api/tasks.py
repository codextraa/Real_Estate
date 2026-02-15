from celery import shared_task, chain
from celery.utils.log import get_task_logger
from django.utils import timezone
from core_db_ai.models import ChatMessage, AIReport
from .agents import groq_chat_agent, generate_qwen_insight
from report_api.regression_model import InvestmentRegressor

logger = get_task_logger(__name__)

@shared_task(bind=True, max_retries=3)
def generate_ai_chat_response(self, message_id, report_id, user_query):
    try:
        # One query to rule them all: SQL JOIN between AIReport and Property
        report = AIReport.objects.select_related('property').get(id=report_id)
        
        # This no longer hits the database; the data is already in memory
        property_obj = report.property 

        # Fetch the message
        ai_message = ChatMessage.objects.get(id=message_id)
        
        # Use update_fields for efficiency if using .save(), 
        # or use the queryset update method:
        ai_message.update(status=ChatMessage.Status.PROCESSING)

        # Dictionary construction (data is already loaded)
        property_details = {
            "title": property_obj.title,
            "beds": property_obj.beds,
            "baths": property_obj.baths,
            "area_sqft": property_obj.area_sqft,
            "price": float(property_obj.price), # Ensure JSON serializable
        }

        report_details = {
            "comparable_data": report.comparable_data,
            "avg_beds": report.avg_beds,
            "avg_baths": report.avg_baths,
            "avg_market_price": str(report.avg_market_price),
            "avg_price_per_sqft": str(report.avg_price_per_sqft),
            "investment_rating": str(report.investment_rating),
        }

        return chain(
            ai_message_analysis.s(
                message_id,
                property_details,
                report_details,
                user_query
            ),
            finalizer_task.s(message_id)
        ).apply_async()
    
    except AIReport.DoesNotExist:
        logger.error(f"Abort: Report {report_id} does not exist.")
        return None
    except ChatMessage.DoesNotExist:
        logger.error(f"Abort: Message {message_id} does not exist.")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        if 'ai_message' in locals():
            ChatMessage.objects.filter(id=message_id).update(status=ChatMessage.Status.FAILED)
        return None
    

@shared_task(bind=True)
def ai_message_analysis(self, message_id, property_details, report_details, user_query):
    # --- PHASE 1: GPT 20B (JSON Convert) ---
    # Extracts updated property_json from user_message + property_details
    property_json = groq_chat_agent(property_details, user_query)
    
    if property_json.get("answer") == "Invalid Request":
        self.request.chain = None
        return "Stopped"

    # --- PHASE 2: Investment Regressor ---
    # Uses report_details for market context (averages)
    regressor = InvestmentRegressor(
        avg_price=float(report_details['avg_market_price']),
        avg_pps=float(report_details['avg_price_per_sqft']),
        avg_beds=float(report_details['avg_beds']),
        avg_baths=float(report_details['avg_baths'])
    )
    
    # Produces the breakdown json
    rating, breakdown_json = regressor.calculate_rating(
        compiled_data=report_details.get("comparable_data", []),
        property_data=property_json
    )

    # --- PHASE 3: Qwen Agent (Insight Generation) ---
    # Give breakdown_json to the final agent to generate 'insight in text'
    # This mirrors your teammate's 'groq_ai_insight_prompt'
    final_insight, usage = generate_qwen_insight(
        breakdown_json, 
        property_json, 
        rating
    )

    # --- PHASE 4: Return for Finalizer ---
    # Finalizer catches this to update the AI message
    return {
        "message_id": message_id,
        "text": final_insight['investment_summary'],
        "rating": rating
    }

@shared_task(bind=True)
def finalizer_task(self, analysis_result, message_id):
    pass