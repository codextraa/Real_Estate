import json
from openai import OpenAI
from tavily import TavilyClient
from celery.utils.log import get_task_logger
from celery import shared_task, chord
from django.conf import settings
from core_db_ai.models import AIReport, Property
from .mockdata import generate_mock_properties
from .utils import extract_location
from .regression_model import InvestmentRegressor


logger = get_task_logger(__name__)
client = OpenAI(api_key=settings.DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
tavily = TavilyClient(api_key=settings.TAVILY_API_KEY)


@shared_task
def search_properties(
    area, city, area_sqft, beds, baths, count, seed_index
):  # pylint: disable=R0913, R0917, R0914
    """
    Worker Task: Calls Tavily and DeepSeek for a specific slice of data.
    """
    try:
        # Variations to ensure the 4 workers find different things
        search_queries = [
            f"list of recently sold homes in {area} {city} with price and sqft beds baths",
            (
                f"real estate listings in {area} {city} {area_sqft} sqft "
                f"{beds} bed {baths} bath sold price"
            ),
            (
                f"site:zillow.com OR site:redfin.com sold properties in "
                f"{area} {city} with price sqft beds baths"
            ),
            (
                f"property records {area} {city} {area_sqft} square feet price "
                f"per sqft beds baths"
            ),
        ]

        # Tavily accurate search
        search_result = tavily.search(
            query=search_queries[seed_index],
            max_results=count,
            search_depth="basic",
            include_usage=True,
        )

        # Tavily Credit Usage
        tavily_credits = search_result.get("usage", {}).get("credits", "unknown")
        logger.info(f"[Tavily] Used {tavily_credits} credits for query {seed_index}")

        context_text = "\n---\n".join(
            [res["content"] for res in search_result["results"]]
        )

        # DeepSeek JSON extraction
        prompt = (
            f"You are a Real Estate Data Extraction Expert. I have gathered raw search data "
            f"for properties in {area}, {city} near {area_sqft} sqft, {beds} beds, "
            f"and {baths} baths.\n\n"
            f"RAW DATA:\n{context_text}\n\n"
            f"TASK:\n"
            f"1. Use ONLY the data provided above.\n"
            f"2. Extract realistic comparable properties from the text.\n"
            f"3. Return ONLY a JSON object with a key 'properties' containing a list.\n\n"
            f"Required Fields per object: [price, area_sqft, beds, baths].\n"
            f"Exclude any other fields."
        )

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1,  # Low temperature for strict extraction accuracy
        )

        # DeepSeek Token Usage
        usage = response.usage
        logger.info(
            f"[DeepSeek] Prompt Tokens: {usage.prompt_tokens} | "
            f"Completion Tokens: {usage.completion_tokens} | "
            f"Total: {usage.total_tokens}"
        )

        # Extract the list from the JSON response
        data = json.loads(response.choices[0].message.content)
        return data.get("properties", [])
    except Exception as e:  # pylint: disable=W0718
        logger.error(f"API Error: {e}. Falling back to mock data.")
        return generate_mock_properties(area_sqft, beds, baths, count)


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
            price = item.get("price", 0)
            sqft = item.get("area_sqft", 0)
            bds = item.get("beds", 0)
            bths = item.get("baths", 0)

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

    prices = [p["price"] for p in compiled_data if p.get("price")]
    sqft = [p["area_sqft"] for p in compiled_data if p.get("area_sqft")]

    if prices:
        avg_price = sum(prices) / len(prices)
    else:
        avg_price = 0

    if sqft:
        avg_sqft = sum(sqft) / len(sqft)
    else:
        avg_sqft = 0

    # Calculate market average PPS
    if avg_sqft > 0:
        avg_pps = avg_price / avg_sqft
    else:
        avg_pps = 0

    logger.info("Market Average Price: %s | Market Average PPS: %s", avg_price, avg_pps)
    return {"avg_market_price": avg_price, "avg_price_per_sqft": avg_pps}


@shared_task
def analyze_beds_baths(compiled_data):
    """Calculates average beds and baths."""
    if not compiled_data:
        return {}

    beds = [p["beds"] for p in compiled_data if p.get("beds") is not None]
    baths = [p["baths"] for p in compiled_data if p.get("baths") is not None]

    if beds:
        avg_beds = round(sum(beds) / len(beds))
    else:
        avg_beds = 0

    if baths:
        avg_baths = round(sum(baths) / len(baths))
    else:
        avg_baths = 0

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


@shared_task
def analyze_insight(compiled_data, property_data):
    """
    Uses DeepSeek to generate the pros/cons insight summary.
    """
    if not compiled_data:
        return {"ai_insight_summary": "No market data available for analysis."}

    title = property_data.get("title", "Subject Property")
    price = property_data.get("price", 0)
    sqft = property_data.get("area_sqft", 0)
    beds = property_data.get("beds", 0)
    baths = property_data.get("baths", 0)

    # Small compiled json data to avoid window bloat
    comps_sample = compiled_data[:20]

    prompt = (
        f"Subject Property: {title} priced at ${price}. "
        f"Specs: {sqft} sqft, {beds} beds, {baths} baths.\n"
        f"Market Comparables JSON: {json.dumps(comps_sample)}\n\n"
        "TASK: Act as a Real Estate Investment Analyst. "
        "Provide a brief summary of the investment potential. "
        "List 2 Pros and 2 Cons comparing the subject to these market comps. "
        "Be concise and professional."
    )

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,  # Increased creativity
        )
        summary = response.choices[0].message.content
        logger.info("DeepSeek summary generated successfully")
    except Exception as e:  # pylint: disable=W0718
        logger.error("DeepSeek Summary Error: %s", e)
        # avg_comp_price = sum(p.get('price', 0) for p in compiled_data) / len(compiled_data)
        # price_diff = "below" if price < avg_comp_price else "above"
        # summary = (
        #     f"PROS:\n"
        #     f"1. Competitive Positioning: The property is priced {price_diff} "
        #     f"the local market average of ${avg_comp_price:,.2f}.\n"
        #     f"2. Solid Utility: With {beds} beds and {baths} baths, the layout "
        #     f"matches high-demand rental profiles for {sqft} sqft homes.\n\n"
        #     f"CONS:\n"
        #     f"1. Market Saturation: Several similar units in the {title} area "
        #     f"may limit immediate appreciation.\n"
        #     f"2. Scale Constraints: At {sqft} sqft, the property may face "
        #     f"competition from larger newly-built comps."
        # )
        summary = "Analysis failed"

    return {"ai_insight_summary": summary}


@shared_task
def report_finalizer(analysis_results, compiled_data, report_id):
    """
    analysis_results: [price_stats, bed_bath_stats, rating_stats, ai_summary_text]
    Map results to the AIReport model
    """
    report = AIReport.objects.get(id=report_id)

    try:
        report.comparable_data = compiled_data

        # Map results from parallel workers
        for result in analysis_results:
            if isinstance(result, dict):
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
def parallel_report_generator(property_id, user_id):
    """
    Parallel Report generator using searching and then analysis
    """
    property_data = Property.objects.filter(id=property_id).first()
    area, city = extract_location(property_data.address)
    area_sqft = property_data.area_sqft
    beds = property_data.beds
    baths = property_data.baths

    # Define 4 parallel chunks (25 properties each = 100 total)
    search_tasks = [
        search_properties.s(area, city, area_sqft, beds, baths, 25, i) for i in range(4)
    ]

    # Define the callback that merges the data
    finalizer = compile_search_data.s()

    # Create the report object
    report = AIReport.objects.create(
        property_id=property_id,
        user_id=user_id,
        extracted_area=area,
        extracted_city=city,
    )

    # Linking the tasks so that search_tasks ends then callback is called
    workflow_result = chord(search_tasks)(
        finalizer
        | run_analysis_group.s(report_id=report.id, property_data=property_data)
    )

    # Return the ID
    return workflow_result.id
