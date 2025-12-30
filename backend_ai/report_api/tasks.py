import json
from openai import OpenAI
from tavily import TavilyClient
from celery.utils.log import get_task_logger
from celery import shared_task, chord
from django.conf import settings
from .mockdata import generate_mock_properties


logger = get_task_logger(__name__)
client = OpenAI(api_key=settings.DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
tavily = TavilyClient(api_key=settings.TAVILY_API_KEY)


@shared_task
def search_properties(area, city, area_sqft, beds, baths, count, seed_index):
    """
    Worker Task: Calls Tavily and DeepSeek for a specific slice of data.
    """
    try:
        # Variations to ensure the 4 workers find different things
        search_queries = [
            f"recently sold homes in {area} {city} near {area_sqft} sqft",
            (
                f"active real estate listings {area} {city} near {area_sqft} "
                f"sqft {beds} bed {baths} bath"
            ),
            (
                f"recent home sales {area} {city} property with {beds} bed "
                f"and {baths} bath data price per sqft"
            ),
            f"real estate market data {area} {city} sold properties",
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
    except Exception as e:
        logger.error(f"API Error: {e}. Falling back to mock data.")
        return generate_mock_properties(area_sqft, beds, baths, count)


@shared_task
def compile_results_callback(results):
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

    logger.info(f"Final dataset compiled: {len(final_list)} unique properties.")
    return final_list


@shared_task
def start_parallel_search(area, city, area_sqft, beds, baths):
    """
    Parallel Task:
    Divides the work into 4 workers and returns the Workflow ID.
    """

    # Define 4 parallel chunks (25 properties each = 100 total)
    search_tasks = [
        search_properties.s(area, city, area_sqft, beds, baths, 25, i) for i in range(4)
    ]

    # Define the callback that merges the data
    finalizer = compile_results_callback.s()

    # Linking the tasks so that search_tasks ends then callback is called
    workflow_result = chord(search_tasks)(finalizer)

    # Return the ID
    return workflow_result.id
