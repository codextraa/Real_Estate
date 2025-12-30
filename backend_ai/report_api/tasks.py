import os
import json
from celery import shared_task, chord
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com"
)


@shared_task
def fetch_deepseek_comps(area, city, area_sqft, count, seed_index):
    """
    Worker Task: Calls DeepSeek for a specific slice of data.
    """
    # Variations to ensure the 4 workers find different things
    strategies = [
        "Focus on recently sold properties.",
        "Focus on active listings.",
        "Focus on properties with premium upgrades.",
        "Focus on properties within a 2-mile radius.",
    ]

    prompt = (
        f"Generate {count} realistic real estate comps in {area}, {city} near {area_sqft} sqft. "
        f"{strategies[seed_index]} Return ONLY a JSON list of objects with the key 'properties'. "
        f"Include: price, area_sqft, year_built, days_on_market."
    )

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=1.0,  # High temperature = more variety
    )

    # Extract the list from the JSON response
    data = json.loads(response.choices[0].message.content)
    return data.get("properties", [])


def compile_results_callback(results):
    """
    Callback Task: Runs only when all 4 fetchers are done.
    Merges and cleans the data.
    """
    final_list = []
    seen_identifiers = set()

    # Remove duplicates from results which is [[25 items], [25 items], [25 items], [25 items]]
    for chunk in results:
        for item in chunk:
            # Unique 'fingerprint' for each property
            fingerprint = f"{item.get('price')}-{item.get('area_sqft')}"

            if fingerprint not in seen_identifiers:
                final_list.append(item)
                seen_identifiers.add(fingerprint)

    return final_list


@shared_task
def start_parallel_search(area, city, area_sqft):
    """
    Parallel Task:
    Divides the work into 4 workers and returns the Workflow ID.
    """

    # Define 4 parallel chunks (25 properties each = 100 total)
    search_tasks = [
        fetch_deepseek_comps.s(area, city, area_sqft, 25, i) for i in range(4)
    ]

    # Define the callback that merges the data
    finalizer = compile_results_callback.s()

    # Linking the tasks so that search_tasks ends then callback is called
    workflow_result = chord(search_tasks)(finalizer)

    # Return the ID
    return workflow_result.id
