import json
from openai import OpenAI
from django.conf import settings

# Reusing the existing client setup
openai = OpenAI(
    api_key=settings.GROQ_API_KEY2, 
    base_url="https://api.groq.com/openai/v1"
)

def groq_chat_agent(property_details, user_query):
    # Convert original dict to string for the AI to read
    current_context = json.dumps(property_details, indent=2)

    system_role = (
        "You are a Real Estate Data Parser. Your job is to extract property features "
        "for a mathematical regression model.\n"
        "STRICT RULES:\n"
        "1. If the user query updates a value (e.g., 'What if it had 5 beds?'), use the NEW value.\n"
        "2. If the user query does NOT change a value, use the ORIGINAL value from property_details.\n"
        "3. Output ONLY a JSON object with keys: [area_sqft, beds, baths, price, answer].\n"
        "4. If the request is unrelated to property features, set 'answer' to 'Invalid Request'."
    )

    user_message = (
        f"ORIGINAL PROPERTY DETAILS:\n{current_context}\n\n"
        f"USER QUERY: {user_query}\n\n"
        "Output the final state in this JSON format:\n"
        "{\n"
        "  'area_sqft': float,\n"
        "  'beds': int,\n"
        "  'baths': float,\n"
        "  'price': float,\n"
        "  'answer': 'Your brief explanation of what was changed or answered',\n"
        "  'data_found': true\n"
        "}"
    )

    response = openai.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": system_role},
            {"role": "user", "content": user_message},
        ],
        response_format={"type": "json_object"},
        temperature=0.0
    )

    return json.loads(response.choices[0].message.content)



def generate_qwen_insight(breakdown_json, property_json, rating):
    """
    Qwen-2.5-Coder-32b Agent (via Groq)
    Translates mathematical breakdown into human-friendly investment insight.
    """
    
    system_role = (
        "You are a Senior Real Estate Investment Analyst. Your job is to translate "
        "raw scoring data from a regression model into a professional executive summary.\n\n"
        "GUIDELINES:\n"
        "1. TONE: Objective, data-driven, and executive.\n"
        "2. Avoid technical jargon like 'regressor' or 'json'.\n"
        "3. Focus on the 'why' behind the rating using the provided breakdown."
    )

    user_prompt = (
        f"PROPERTY: {property_json.get('title', 'Subject Property')}\n"
        f"FINAL RATING: {rating} / 5.0\n\n"
        f"REGRESSION BREAKDOWN:\n{json.dumps(breakdown_json, indent=2)}\n\n"
        "TASK: Provide a JSON object with this structure:\n"
        "{\n"
        "  'investment_summary': 'A 3-sentence summary of the property value.',\n"
        "  'pros': ['strength 1', 'strength 2'],\n"
        "  'cons': ['risk 1', 'risk 2']\n"
        "}"
    )

    response = openai.chat.completions.create(
        # Use the specific Qwen model ID available on Groq
        model="qwen-2.5-32b", 
        messages=[
            {"role": "system", "content": system_role},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.7, # Higher temperature for more natural 'insight' text
    )

    return json.loads(response.choices[0].message.content), response.usage