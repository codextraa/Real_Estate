import json
from openai import OpenAI
from django.conf import settings

openai = OpenAI(
    api_key=settings.GROQ_API_KEY2, base_url="https://api.groq.com/openai/v1"
)


def chat_json_extractor_agent(property_details, user_query):
    # Convert original dict to string for the AI to read
    current_property_details = json.dumps(property_details, indent=2)

    system_role = (
        "You are a Real Estate Data Parser. Your job is to extract property features "
        "for a mathematical regression model.\n"
        "STRICT RULES:\n"
        "1. If the user query updates a value "
        "(e.g., 'What if it had 5 beds?'), use the NEW value.\n"
        "2. If the user query does NOT change a value, "
        "use the ORIGINAL value from property_details.\n"
        "3. Output ONLY a JSON object with keys: [area_sqft, beds, baths, price].\n"
        "4. CRITICAL: If the user query is unrelated to "
        "property features (area sqft, beds, baths, price), "
        "set the 'error' key to 'Invalid request. Please try again.' "
        "and leave other fields null."
    )

    user_message = (
        f"ORIGINAL PROPERTY DETAILS:\n{current_property_details}\n\n"
        f"USER QUERY: {user_query}\n\n"
        "Output the final state in this JSON format:\n"
        "{\n"
        "  'area_sqft': float or null,\n"
        "  'beds': int or null,\n"
        "  'baths': int or null,\n"
        "  'price': float or null,\n"
        "  'error': string or null\n"
        "}"
    )

    response = openai.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": system_role},
            {"role": "user", "content": user_message},
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
    )

    # Groq Credit Usage
    usage = response.usage

    return json.loads(response.choices[0].message.content), usage
