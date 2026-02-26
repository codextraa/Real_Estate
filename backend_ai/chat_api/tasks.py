import datetime
from celery import shared_task, chain
from celery.utils.log import get_task_logger
from celery.exceptions import MaxRetriesExceededError
from report_api.regression_model import InvestmentRegressor
from report_api.agents import groq_ai_insight_prompt
from core_db_ai.models import ChatMessage, AIReport
from .agents import chat_json_extractor_agent

logger = get_task_logger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=61,
    rate_limit="8/m",
    retry_jitter=False,
)
def ai_message_extractor(self, message_id, property_details, user_query):
    """
    Worker Task: Calls Groq GPT for extraction.
    """
    try:
        property_json, usage = chat_json_extractor_agent(property_details, user_query)

        # pylint: disable=R0801
        logger.info(
            "[Groq GPT] Prompt Tokens: %s | Completion Tokens: %s | Total: %s",
            usage.prompt_tokens,
            usage.completion_tokens,
            usage.total_tokens,
        )
        logger.info("Groq Json extraction complete.")
        # pylint: enable=R0801

        error = property_json.get("error")
        if error:
            self.request.chain = None
            message = ChatMessage.objects.get(id=message_id)
            message.update(status=ChatMessage.Status.FAILED, content=error)
            return "Stopped"

        property_json["title"] = property_details["title"]
        return property_json
    except Exception as e:  # pylint: disable=W0718
        # pylint: disable=R0801
        logger.warning(
            "Attempt %s/%s failed Groq Rate Limit/Error: %s. Retrying again",
            self.request.retries,
            self.max_retries,
            e,
        )
        # pylint: enable=R0801
        try:
            return self.retry(exc=e)
        except MaxRetriesExceededError as err:
            logger.error("Groq GPT Summary Error: %s", err)
            self.request.chain = None
            message = ChatMessage.objects.get(id=message_id)
            message.update(
                status=ChatMessage.Status.FAILED,
                content="Agent failed to respond. Please try again.",
            )
            return "Stopped"


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=61,
    rate_limit="8/m",
    retry_jitter=False,
    autoretry_for=(),
)
def ai_message_analysis(
    self,
    property_json,
    message_id,
    report_details,
    user_query,
    rating=None,
    breakdown=None,
):  # pylint: disable=R0913, R0917
    """
    Passes the json to Investment Regressor for rating.
    Then Calls Groq Qwen for AI Insight Summary.
    """
    compiled_data = report_details.get("comparable_data", [])

    if rating and len(breakdown) > 0:
        logger.info(
            "Retrying Groq Qwen only. Skipping Investment Regressor for rating and breakdown."
        )
    else:
        regressor = InvestmentRegressor(
            avg_price=float(report_details["avg_market_price"]),
            avg_pps=float(report_details["avg_price_per_sqft"]),
            avg_beds=float(report_details["avg_beds"]),
            avg_baths=float(report_details["avg_baths"]),
        )

        compiled_data = report_details.get("comparable_data", [])
        try:
            rating, breakdown = regressor.calculate_rating(compiled_data, property_json)
            if not rating or not breakdown or len(breakdown) == 0:
                raise ValueError("Empty rating or breakdown generated")
        except Exception as e:  # pylint: disable=W0718
            logger.error("FATAL: Investment Rating Error: %s", e)
            self.request.chain = None
            message = ChatMessage.objects.get(id=message_id)
            message.update(
                status=ChatMessage.Status.FAILED,
                content="Agent failed to respond. Please try again.",
            )
            return "Stopped"

    # pylint: disable=R0801
    logger.info("Investment Rating: %s", rating)
    logger.info("Investment Breakdown: %s", str(breakdown))

    if len(compiled_data) > 50:
        comps_sample = compiled_data[:50]
    else:
        comps_sample = compiled_data
    # pylint: enable=R0801

    try:
        final_insight, usage = groq_ai_insight_prompt(
            comps_sample, property_json, rating, breakdown, "Qwen"
        )

        # pylint: disable=R0801
        logger.info(
            "[Groq Qwen] Prompt Tokens: %s | Completion Tokens: %s | Total: %s",
            usage.prompt_tokens,
            usage.completion_tokens,
            usage.total_tokens,
        )
        logger.info("Groq Qwen chat answer generated successfully")
        # pylint: enable=R0801

        return {
            "text": final_insight,
            "rating": rating,
        }
    except Exception as e:  # pylint: disable=W0718
        # pylint: disable=R0801
        logger.warning(
            "Attempt %s/%s failed Groq Rate Limit/Error: %s. Retrying again",
            self.request.retries,
            self.max_retries,
            e,
        )
        # pylint: enable=R0801
        try:
            return self.retry(
                args=[
                    property_json,
                    message_id,
                    report_details,
                    user_query,
                ],
                kwargs={
                    "rating": rating,
                    "breakdown": breakdown,
                },
                exc=e,
            )
        except MaxRetriesExceededError as err:
            logger.error("Groq GPT Summary Error: %s", err)
            self.request.chain = None
            message = ChatMessage.objects.get(id=message_id)
            message.update(
                status=ChatMessage.Status.FAILED,
                content="Agent failed to respond. Please try again.",
            )
            return "Stopped"


@shared_task
def finalizer_task(analysis_result, message_id):  # pylint: disable=W0613
    """
    Takes the JSON analysis from Qwen, formats it into a professional message,
    and updates the ChatMessage model.
    """
    if analysis_result == "Stopped":
        return "Aborted"

    try:
        message = ChatMessage.objects.get(id=message_id)
        insight = analysis_result.get("text", {})
        rating = analysis_result.get("rating", 0)

        # Optimization: In chat, the "Investment Summary" is the actual answer.
        # We lead with the answer, then provide the data-backed reasoning.
        summary_text = (
            f"{insight.get('investment_summary', '')}\n\n"
            f"**New Projected Rating: {rating} / 5**\n\n"
            f"**Analysis of Adjustments:**\n{insight.get('weighted_analysis', '')}\n\n"
            "**Key Strengths:**\n- " + "\n- ".join(insight.get("pros", [])) + "\n\n"
            "**Potential Risks:**\n- " + "\n- ".join(insight.get("cons", []))
        )

        message.content = summary_text
        message.status = ChatMessage.Status.COMPLETED
        message.timestamp = datetime.datetime.now()
        message.save()

        return f"Message {message_id} Success"
    except Exception as e:
        logger.error("Finalizer failed: %s", str(e))
        ChatMessage.objects.filter(id=message_id).update(
            status=ChatMessage.Status.FAILED,
            content="Error finalizing the AI response."
        )
        return f"Message {message_id} Failed"


@shared_task
def generate_ai_chat_response(message_id, report_id, user_query):
    try:
        report = AIReport.objects.select_related("property").get(id=report_id)
        property_obj = report.property
        ai_message = ChatMessage.objects.get(id=message_id)
        ai_message.update(status=ChatMessage.Status.PROCESSING)

        property_details = {
            "title": property_obj.title,
            "beds": property_obj.beds,
            "baths": property_obj.baths,
            "area_sqft": property_obj.area_sqft,
            "price": float(property_obj.price),
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
            ai_message_extractor.s(message_id, property_details, user_query),
            ai_message_analysis.s(message_id, report_details, user_query),
            finalizer_task.s(message_id),
        ).apply_async()
    except AIReport.DoesNotExist:
        logger.error(f"Abort: Report {report_id} does not exist.")
        return None
    except ChatMessage.DoesNotExist:
        logger.error(f"Abort: Message {message_id} does not exist.")
        return None
    except Exception as e:  # pylint: disable=W0718
        logger.error(f"Unexpected error: {str(e)}")
        if "ai_message" in locals():
            ChatMessage.objects.filter(id=message_id).update(
                status=ChatMessage.Status.FAILED
            )
        return None
