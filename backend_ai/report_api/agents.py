import json
from openai import OpenAI
from tavily import TavilyClient
from django.conf import settings
from .utils import clean_context

openai = OpenAI(
    api_key=settings.GROQ_API_KEY, base_url="https://api.groq.com/openai/v1"
)
tavily = TavilyClient(api_key=settings.TAVILY_API_KEY)


def tavily_search(
    area, city, area_sqft, beds, baths, count, seed_index
):  # pylint: disable=R0913, R0917
    search_queries = [
        (
            f"recently sold properties in {area} {city} with price area_sqft "
            "beds baths 'sold date'"
        ),
        (
            f"site:homes.com {area} {city} 'recently sold' {area_sqft} sqft "
            f"{beds} beds {baths} baths price"
        ),
        (
            f"site:zillow.com {area} {city} 'recently sold' {area_sqft} sqft "
            f"{beds} beds {baths} baths with price"
        ),
        (
            f"site:redfin.com {area} {city} 'recently sold homes' {area_sqft} sqft "
            f"{beds} beds {baths} baths with price"
        ),
    ]

    # Tavily accurate search
    search_result = tavily.search(
        query=search_queries[seed_index],
        max_results=count,
        search_depth="advanced",
        include_raw_content=False,
        include_usage=True,
    )

    # Tavily Credit Usage
    tavily_credits = search_result.get("usage", {}).get("credits", "unknown")

    # Tavily Context
    context_text = "\n---\n".join(
        [
            f"Source: {res['url']}\nContent: {res['content']}"
            for res in search_result["results"]
        ]
    )

    context_text = clean_context(context_text)

    return context_text, tavily_credits


def groq_json_formatter(context_text, area, city):
    # Groq llama JSON extraction
    prompt = (
        f"You are a Real Estate Data Expert. Extract comparable properties for {area}, {city}.\n\n"
        f"RAW DATA:\n{context_text}\n\n"
        "STRICT RULES:\n"
        "1. Use ONLY the data provided above.\n"
        "2. Return ONLY a JSON object with a key 'properties' containing a list.\n"
        "3. Required Fields per object: [price, area_sqft, beds, baths].\n"
        "4. If ANY REQUIRED field is missing, 'None', or 'unknown', DO NOT EXTRACT THAT PROPERTY.\n"
        "5. Exclude any other fields."
    )

    response = openai.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.0,  # Low temperature for strict extraction accuracy
        max_tokens=1000,
    )

    # Groq Credit Usage
    usage = response.usage

    # Extract the list from the JSON response
    data = json.loads(response.choices[0].message.content)
    return data.get("properties", []), usage


def groq_ai_insight_prompt(
    comps_sample, title, price, sqft, beds, baths
):  # pylint: disable=R0913, R0917
    """Groq Llamma Agent"""

    prompt = (
        f"Subject Property: {title} priced at ${price}.\n"
        f"Specs: {sqft} sqft, {beds} beds, {baths} baths.\n"
        f"Market Comps: {json.dumps(comps_sample)}\n\n"
        "TASK: Act as a Real Estate Analyst. Provide a JSON object with keys: "
        "'investment_summary' (string), 'pros' (list of 2 strings), 'cons' (list of 2 strings)."
    )

    response = openai.chat.completions.create(
        model="qwen/qwen3-32b",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.8,  # Higher temperature for more creative responses
    )

    # Groq Credit Usage
    usage = response.usage

    return json.loads(response.choices[0].message.content), usage
