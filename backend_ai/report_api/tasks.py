# import time
# import random
from celery import shared_task, chord, chain
from celery.utils.log import get_task_logger

# from celery.exceptions import MaxRetriesExceededError
from core_db_ai.models import AIReport

# from .agents import tavily_search, groq_json_formatter, groq_ai_insight_prompt
# from .regression_model import InvestmentRegressor
from .utils import (
    # split_context,
    clean_properties,
    # average_prices_beds_baths,
    generate_mock_summary,
    generate_mock_properties,
)


logger = get_task_logger(__name__)


@shared_task()
def search_properties(
    report_id, property_data, count, seed_index
):  # pylint: disable=W0613
    """
    Worker Task: Mocks Tavily and Groq llama for a specific slice of data.
    """
    area_sqft = property_data.get("area_sqft")
    beds = property_data.get("beds")
    baths = property_data.get("baths")
    return generate_mock_properties(area_sqft, beds, baths, count)


# @shared_task(
#     bind=True,
#     rate_limit="15/m",  # Max 15 calls/m to avoid Groq 429s
#     max_retries=5,
#     default_retry_delay=61,  # Groq hits a limit, wait for full minute reset
#     retry_jitter=False,  # Predictable 61s wait, no randomness needed
#     autoretry_for=(),
# )
# def search_properties(
#     self,
#     report_id,
#     property_data,
#     count,
#     seed_index,
#     existing_context=None,
#     final_properties=None,
#     completed_chunks=None,
# ):  # pylint: disable=R0913, R0914, R0917
#     """
#     Worker Task: Calls Tavily and Groq llama for a specific slice of data.
#     """
#     area = property_data.get("area")
#     city = property_data.get("city")
#     area_sqft = property_data.get("area_sqft")
#     beds = property_data.get("beds")
#     baths = property_data.get("baths")
#     context_text = None

#     if existing_context:
#         logger.info("Retrying Groq only. Skipping Tavily for query %s.", seed_index)
#         context_text = existing_context
#     else:
#         try:
#             # Variations to ensure the 4 workers find different things
#             context_text, tavily_credits = tavily_search(
#                 area, city, area_sqft, beds, baths, count, seed_index
#             )

#             logger.info(
#                 "[Tavily] Used %s credits for query %s", tavily_credits, seed_index
#             )
#         except Exception as e:  # pylint: disable=W0718
#             logger.warning("Search Task Error: %s. Retrying...", e)
#             try:
#                 raise self.retry(exc=e)
#             except MaxRetriesExceededError:
#                 logger.error(
#                     "FATAL: Fork %s exceeded max retries. Providing mock data.",
#                     seed_index,
#                 )
#                 AIReport.objects.get(id=report_id).update(
#                     status=AIReport.Status.FAILED,
#                     ai_insight_summary="Automated data search failed. Please try again later.",
#                 )
#                 return generate_mock_properties(area_sqft, beds, baths, count)

#     if final_properties is None:
#         final_properties = []
#     if completed_chunks is None:
#         completed_chunks = []

#     chunks = split_context(context_text)
#     time.sleep(random.uniform(1.0, 5.0))

#     for i, chunk in enumerate(chunks):
#         if i in completed_chunks:
#             continue

#         try:
#             if i > 0:
#                 time.sleep(2)

#             properties_json, usage = groq_json_formatter(chunk, area, city)

#             logger.info(
#                 "Fork %s Chunk %s: [Groq Llama] Prompt Tokens:%s "
#                 "| Completion Tokens:%s | Total:%s",
#                 seed_index,
#                 i,
#                 usage.prompt_tokens,
#                 usage.completion_tokens,
#                 usage.total_tokens,
#             )

#             final_properties.extend(properties_json)
#             completed_chunks.append(i)
#         except Exception as e:  # pylint: disable=W0718
#             logger.warning(
#                 "Attempt %s/%s failed for Fork %s Chunk %s. Groq Rate "
#                 "Limit/Error: %s. Retrying extraction with SAVED context.",
#                 self.request.retries,
#                 self.max_retries,
#                 seed_index,
#                 i,
#                 e,
#             )

#             try:
#                 raise self.retry(
#                     args=[report_id, property_data, count, seed_index],
#                     kwargs={
#                         "existing_context": context_text,
#                         "final_properties": final_properties,
#                         "completed_chunks": completed_chunks,
#                     },
#                     exc=e,
#                 )
#             except MaxRetriesExceededError:
#                 logger.error(
#                     "FATAL: Fork %s exceeded max retries. Providing mock data.",
#                     seed_index,
#                 )
#                 AIReport.objects.get(id=report_id).update(
#                     status=AIReport.Status.FAILED,
#                     ai_insight_summary="Automated data search failed. Please try again later.",
#                 )
#                 return generate_mock_properties(area_sqft, beds, baths, count)

#     return final_properties


@shared_task
def compile_search_data(results, property_data):
    """
    Merges results into a single LIST of dictionaries.
    Uses a safe fingerprint that handles missing keys.
    """
    final_list = []
    seen_identifiers = set()

    for chunk in results:
        if not chunk:
            continue
        for item in chunk:
            try:
                price, sqft, bds, bths = clean_properties(item, property_data)
            except (ValueError, TypeError, IndexError):
                continue

            fingerprint = f"{price}-{sqft}-{bds}-{bths}"
            if fingerprint not in seen_identifiers:
                final_list.append(
                    {"price": price, "area_sqft": sqft, "beds": bds, "baths": bths}
                )
                seen_identifiers.add(fingerprint)

    logger.info("Final dataset compiled: %s unique properties.", len(final_list))
    return final_list


@shared_task()
def report_analysis(compiled_data, report_id, property_data):  # pylint: disable=W0613
    """Mocks Groq GPT to generate the analysis."""
    ai_insight_summary = generate_mock_summary(compiled_data, property_data)
    return {
        "avg_market_price": 0,
        "avg_price_per_sqft": 0,
        "avg_beds": 0,
        "avg_baths": 0,
        "investment_rating": 0,
        "ai_insight_summary": ai_insight_summary,
    }


# @shared_task(bind=True, max_retries=3, default_retry_delay=61, rate_limit="8/m")
# def report_analysis(
#     self, compiled_data, report_id, property_data
# ):  # pylint: disable=R0914, R1710
#     """
#     Calculates average prices, beds, baths.
#     Calculates investment rating.
#     Produce AI insight summary on them with pros and cons.
#     Using Groq gpt oss 120b
#     """
#     report = AIReport.objects.get(id=report_id)
#     if not compiled_data or report.status == AIReport.Status.FAILED:
#         return {
#             "avg_market_price": 0,
#             "avg_price_per_sqft": 0,
#             "avg_beds": 0,
#             "avg_baths": 0,
#             "investment_rating": 0,
#             "ai_insight_summary": report.ai_insight_summary
#             or "No market data available for analysis.",
#         }

#     avg_price, avg_pps, avg_beds, avg_baths = average_prices_beds_baths(compiled_data)

#     if avg_price == 0 or avg_pps == 0 or avg_beds == 0 or avg_baths == 0:
#         return {
#             "avg_market_price": avg_price,
#             "avg_price_per_sqft": avg_pps,
#             "avg_beds": avg_beds,
#             "avg_baths": avg_baths,
#             "investment_rating": 0,
#             "ai_insight_summary": "No market data available for analysis.",
#         }

#     logger.info(
#         "Market Average Price: %s ||| Market Average PPS: %s ||| "
#         "Average Beds: %s ||| Average Baths: %s",
#         avg_price,
#         avg_pps,
#         avg_beds,
#         avg_baths,
#     )

#     regressor = InvestmentRegressor(
#         float(avg_price), float(avg_pps), avg_beds, avg_baths
#     )
#     try:
#         rating, breakdown = regressor.calculate_rating(compiled_data, property_data)
#         if not rating or not breakdown or len(breakdown) == 0:
#             raise ValueError("Empty rating or breakdown generated")
#     except Exception as e:  # pylint: disable=W0718
#         logger.error("FATAL: Investment Rating Error: %s", e)
#         return {
#             "avg_market_price": avg_price,
#             "avg_price_per_sqft": avg_pps,
#             "avg_beds": avg_beds,
#             "avg_baths": avg_baths,
#             "investment_rating": 0,
#             "ai_insight_summary": "No market data available for analysis.",
#         }

#     logger.info("Investment Rating: %s", rating)
#     logger.info("Investment Breakdown: %s", str(breakdown))

#     # Small compiled json data to avoid window bloat
#     if len(compiled_data) > 50:
#         comps_sample = compiled_data[:50]
#     else:
#         comps_sample = compiled_data

#     try:
#         ai_json, usage = groq_ai_insight_prompt(
#             comps_sample, property_data, rating, breakdown
#         )

#         logger.info(
#             "[Groq GPT] Prompt Tokens: %s | Completion Tokens: %s | Total: %s",
#             usage.prompt_tokens,
#             usage.completion_tokens,
#             usage.total_tokens,
#         )
#         logger.info("Groq GPT summary generated successfully")

#         return {
#             "avg_market_price": avg_price,
#             "avg_price_per_sqft": avg_pps,
#             "avg_beds": avg_beds,
#             "avg_baths": avg_baths,
#             "investment_rating": rating,
#             "ai_insight_summary": ai_json,
#         }
#     except Exception as e:  # pylint: disable=W0718
#         logger.warning(
#             "Attempt %s/%s failed Groq Rate Limit/Error: %s. Retrying again",
#             self.request.retries,
#             self.max_retries,
#             e,
#         )
#         try:
#             self.retry(exc=e)
#         except MaxRetriesExceededError as err:
#             logger.error("Groq GPT Summary Error: %s", err)
#             ai_insight_summary = generate_mock_summary(compiled_data, property_data)
#             return {
#                 "avg_market_price": avg_price,
#                 "avg_price_per_sqft": avg_pps,
#                 "avg_beds": avg_beds,
#                 "avg_baths": avg_baths,
#                 "investment_rating": rating,
#                 "ai_insight_summary": ai_insight_summary,
#             }

#     return None


@shared_task
def report_finalizer(analysis_result, compiled_data, report_id):
    """
    analysis_results: price_stats, bed_bath_stats, rating_stats, ai_summary_text
    Map results to the AIReport model
    """
    report = AIReport.objects.get(id=report_id)

    try:  # pylint: disable=R1702
        report.comparable_data = compiled_data

        for key, value in analysis_result.items():
            if hasattr(report, key) and key != "ai_insight_summary":
                setattr(report, key, value)
            else:
                if key == "ai_insight_summary":
                    if isinstance(value, dict):
                        insight = analysis_result["ai_insight_summary"]

                        summary_text = (
                            f"{insight.get('investment_summary', '')}\n\n"
                            f"SCORE BREAKDOWN:\n{insight.get('weighted_analysis', '')}\n\n"
                            "PROS:\n- "
                            + "\n- ".join(insight.get("pros", []))
                            + "\n\nCONS:\n- "
                            + "\n- ".join(insight.get("cons", []))
                        )
                        report.ai_insight_summary = summary_text

        report.status = AIReport.Status.COMPLETED
        report.save()

        logger.info("Report %s fully finalized.", report_id)
        return f"Report {report_id} Success"
    except Exception as e:  # pylint: disable=W0718
        logger.error("Finalizer failed: %s", e)
        report.status = AIReport.Status.FAILED
        report.ai_insight_summary = "Report analysis failed"
        report.save()
        return f"Report {report_id} Failed"


@shared_task
def analysis(compiled_data, report_id, property_data):
    return chain(
        report_analysis.s(
            compiled_data=compiled_data,
            report_id=report_id,
            property_data=property_data,
        ),
        report_finalizer.s(compiled_data=compiled_data, report_id=report_id),
    ).apply_async()


@shared_task
def parallel_report_generator(report_id, property_data):
    """
    Parallel Report generator using searching and then analysis
    """
    report = AIReport.objects.filter(id=report_id)

    if not report.exists():
        return None
    report.update(status=AIReport.Status.PROCESSING)

    # Define 4 parallel chunks (25 properties each = 100 total)
    search_tasks = [
        search_properties.s(report_id, property_data, 25, i).set(countdown=i * 20)
        for i in range(4)
    ]

    # Define the callback that merges the data
    finalizer = compile_search_data.s(property_data=property_data)

    # Linking the tasks so that search_tasks ends then callback is called
    workflow_result = chord(search_tasks)(
        finalizer | analysis.s(report_id=report_id, property_data=property_data)
    )

    return workflow_result.id
