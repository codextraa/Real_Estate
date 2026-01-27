import time
import random
from celery import shared_task, chord
from celery.utils.log import get_task_logger
from celery.exceptions import MaxRetriesExceededError
from core_db_ai.models import AIReport

from .agents import tavily_search, groq_json_formatter, groq_ai_insight_prompt
from .regression_model import InvestmentRegressor
from .utils import (
    split_context,
    average_prices,
    average_beds_baths,
    generate_mock_summary,
    generate_mock_properties,
)


logger = get_task_logger(__name__)


# @shared_task()
# def search_properties(property_data, count, seed_index):  # pylint: disable=W0613
#     """
#     Worker Task: Mocks Tavily and Groq llama for a specific slice of data.
#     """
#     area_sqft = property_data.get("area_sqft")
#     beds = property_data.get("beds")
#     baths = property_data.get("baths")
#     return generate_mock_properties(area_sqft, beds, baths, count)


@shared_task(
    bind=True,
    rate_limit="15/m",  # Max 15 calls/m to avoid Groq 429s
    max_retries=5,
    default_retry_delay=61,  # Groq hits a limit, wait for full minute reset
    retry_jitter=False,  # Predictable 61s wait, no randomness needed
    autoretry_for=(),
)
def search_properties(
    self,
    property_data,
    count,
    seed_index,
    existing_context=None,
    final_properties=None,
    completed_chunks=None,
):  # pylint: disable=R0913, R0914, R0917
    """
    Worker Task: Calls Tavily and Groq llama for a specific slice of data.
    """
    area = property_data.get("area")
    city = property_data.get("city")
    area_sqft = property_data.get("area_sqft")
    beds = property_data.get("beds")
    baths = property_data.get("baths")
    context_text = None

    if existing_context:
        logger.info("Retrying Groq only. Skipping Tavily for query %s.", seed_index)
        context_text = existing_context
    else:
        try:
            # Variations to ensure the 4 workers find different things
            context_text, tavily_credits = tavily_search(
                area, city, area_sqft, beds, baths, count, seed_index
            )

            logger.info(
                "[Tavily] Used %s credits for query %s", tavily_credits, seed_index
            )
        except Exception as e:  # pylint: disable=W0718
            logger.warning("Search Task Error: %s. Retrying...", e)
            try:
                raise self.retry(exc=e)
            except MaxRetriesExceededError:
                logger.error(
                    "FATAL: Fork %s exceeded max retries. Providing mock data.",
                    seed_index,
                )
                return generate_mock_properties(area_sqft, beds, baths, count)

    if final_properties is None:
        final_properties = []
    if completed_chunks is None:
        completed_chunks = []

    chunks = split_context(context_text, parts=2)
    time.sleep(random.uniform(1.0, 5.0))

    for i, chunk in enumerate(chunks):
        if i in completed_chunks:
            continue

        try:
            if i > 0:
                time.sleep(2)

            properties_json, usage = groq_json_formatter(chunk, area, city)

            logger.info(
                "Fork %s Chunk %s: [Groq Search] Prompt Tokens:%s "
                "| Completion Tokens:%s | Total:%s",
                seed_index,
                i,
                usage.prompt_tokens,
                usage.completion_tokens,
                usage.total_tokens,
            )

            final_properties.extend(properties_json)
            completed_chunks.append(i)
        except Exception as e:  # pylint: disable=W0718
            logger.warning(
                "Attempt %s/%s failed for Fork %s Chunk %s. Groq Rate "
                "Limit/Error: %s. Retrying extraction with SAVED context.",
                self.request.retries,
                self.max_retries,
                seed_index,
                i,
                e,
            )

            try:
                raise self.retry(
                    args=[property_data, count, seed_index],
                    kwargs={
                        "existing_context": context_text,
                        "final_properties": final_properties,
                        "completed_chunks": completed_chunks,
                    },
                    exc=e,
                )
            except MaxRetriesExceededError:
                logger.error(
                    "FATAL: Fork %s exceeded max retries. Providing mock data.",
                    seed_index,
                )
                return generate_mock_properties(area_sqft, beds, baths, count)

    return final_properties


@shared_task
def compile_search_data(results):
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
                price = int(
                    str(item.get("price", 0))
                    .replace("$", "")
                    .replace(",", "")
                    .split(".", maxsplit=1)[0]
                )
                sqft = int(float(str(item.get("area_sqft", 0)).replace(",", "")))
                bds = int(float(str(item.get("beds", 0))))
                bths = int(float(str(item.get("baths", 0))))
            except (ValueError, TypeError):
                continue

            if price <= 0 or sqft <= 0 or bds <= 0 or bths <= 0:
                continue

            fingerprint = f"{price}-{sqft}-{bds}-{bths}"
            if fingerprint not in seen_identifiers:
                final_list.append(
                    {"price": price, "area_sqft": sqft, "beds": bds, "baths": bths}
                )
                seen_identifiers.add(fingerprint)

    logger.info("Final dataset compiled: %s unique properties.", len(final_list))
    return final_list


@shared_task
def analyze_prices(compiled_data):
    """Calculates average price and price per sqft."""
    if not compiled_data:
        return {}

    avg_price, avg_pps = average_prices(compiled_data)

    logger.info("Market Average Price: %s | Market Average PPS: %s", avg_price, avg_pps)
    return {"avg_market_price": avg_price, "avg_price_per_sqft": avg_pps}


@shared_task
def analyze_beds_baths(compiled_data):
    """Calculates average beds and baths."""
    if not compiled_data:
        return {}

    avg_beds, avg_baths = average_beds_baths(compiled_data)

    logger.info("Average Beds: %s | Average Baths: %s", avg_beds, avg_baths)
    return {"avg_beds": avg_beds, "avg_baths": avg_baths}


@shared_task
def analyze_investment_rating(compiled_data, property_data):
    """
    Uses InvestmentRegressor to get the 0.0 - 5.0 rating.
    """
    regressor = InvestmentRegressor()
    rating = regressor.calculate_rating(compiled_data, property_data)

    logger.info("Rating: %s", rating)
    return {"investment_rating": rating}


# @shared_task()
# def analyze_insight(compiled_data, property_data):
#     """Mocks Groq llama to generate the pros/cons insight summary."""
#     title = property_data.get("title")
#     price = property_data.get("price")
#     beds = property_data.get("beds")
#     baths = property_data.get("baths")

#     return generate_mock_summary(compiled_data, title, price, beds, baths)


@shared_task(rate_limit="15/m")
def analyze_insight(compiled_data, property_data):
    """
    Uses Groq llama to generate the pros/cons insight summary.
    """
    if not compiled_data:
        return {"ai_insight_summary": "No market data available for analysis."}

    title = property_data.get("title")
    price = property_data.get("price")
    sqft = property_data.get("area_sqft")
    beds = property_data.get("beds")
    baths = property_data.get("baths")

    # Small compiled json data to avoid window bloat
    comps_sample = compiled_data[:20]

    try:
        json, usage = groq_ai_insight_prompt(
            comps_sample, title, price, sqft, beds, baths
        )

        logger.info(
            "[Groq Search] Prompt Tokens: %s | Completion Tokens: %s | Total: %s",
            usage.prompt_tokens,
            usage.completion_tokens,
            usage.total_tokens,
        )
        logger.info("Groq llama summary generated successfully")

        return json
    except Exception as e:  # pylint: disable=W0718
        logger.error("Groq llama Summary Error: %s", e)
        return generate_mock_summary(compiled_data, title, price, beds, baths)


@shared_task
def report_finalizer(analysis_results, compiled_data, report_id):
    """
    analysis_results: [price_stats, bed_bath_stats, rating_stats, ai_summary_text]
    Map results to the AIReport model
    """
    report = AIReport.objects.get(id=report_id)

    try:  # pylint: disable=R1702
        report.comparable_data = compiled_data

        # Map results from parallel workers
        for result in analysis_results:
            if isinstance(result, dict):
                if "investment_summary" in result:
                    # Groq Summary
                    summary = (
                        f"{result['investment_summary']}\n\nPROS:\n- "
                        + "\n- ".join(result["pros"])
                        + "\n\nCONS:\n- "
                        + "\n- ".join(result["cons"])
                    )
                    report.ai_insight_summary = summary
                else:
                    for key, value in result.items():
                        if hasattr(report, key):
                            setattr(report, key, value)

        report.status = AIReport.Status.COMPLETED
        report.save()

        logger.info("Report %s fully finalized.", report_id)
        return f"Report {report_id} Success"
    except Exception as e:  # pylint: disable=W0718
        logger.error("Finalizer failed: %s", e)
        report.status = AIReport.Status.FAILED
        report.ai_insight_summary = "Analysis failed"
        report.save()
        return f"Report {report_id} Failed"


@shared_task
def run_analysis_group(compiled_data, report_id, property_data):
    """
    Triggers the 4-way parallel analysis.
    """
    analysis_header = [
        analyze_prices.s(compiled_data),
        analyze_beds_baths.s(compiled_data),
        analyze_investment_rating.s(compiled_data, property_data),
        analyze_insight.s(compiled_data, property_data),
    ]

    # Merging the results
    return chord(analysis_header)(
        report_finalizer.s(
            compiled_data=compiled_data,
            report_id=report_id,
        )
    )


@shared_task
def parallel_report_generator(report_id, property_data):
    """
    Parallel Report generator using searching and then analysis
    """
    AIReport.objects.filter(id=report_id).update(status="PROCESSING")

    # Define 4 parallel chunks (25 properties each = 100 total)
    search_tasks = [search_properties.s(property_data, 25, i) for i in range(4)]

    # Define the callback that merges the data
    finalizer = compile_search_data.s()

    # Linking the tasks so that search_tasks ends then callback is called
    workflow_result = chord(search_tasks)(
        finalizer
        | run_analysis_group.s(report_id=report_id, property_data=property_data)
    )

    # Return the ID
    return workflow_result.id
