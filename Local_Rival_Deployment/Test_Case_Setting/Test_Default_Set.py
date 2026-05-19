from dotenv import load_dotenv
import os
import requests
import json
from pydantic import BaseModel
from typing import List, Union
from openai import OpenAI

# =========================
# 🔐 ENV
# =========================
load_dotenv()


client = OpenAI()

# =========================
# 🧠 MODELS
# =========================

class DefaultValue(BaseModel):
    value: Union[int, float, str, List[int], List[float], List[str]]

# 🔥 New Model for the generated event name
class EventName(BaseModel):
    name: str

# =========================
# 🧠 AI GENERATION
# =========================

def generate_default_for_field(code: str, field_schema: dict):
    response = client.responses.parse(
        model="gpt-5-chat-latest",
        input=[
            {
                "role": "system",
                "content": """You are an Expert API Data Specialist and Backend Developer. 
Your task is to analyze a JSON Schema field and its corresponding code context to generate a SINGLE, highly realistic, and perfectly type-safe default value.

CRITICAL RULES FOR THE DEFAULT VALUE:

1. Strict Type Matching:
   - Schema type 'integer' or 'number' → Return a numeric value.
   - Schema type 'string' → Return a string.
   - Schema type 'array' → Return a list. You MUST inspect the 'items' type (e.g., if array of numbers, return [1, 2, 3]).

2. Contextual Realism (Crucial):
   - DO NOT return lazy generic values like "string", "test", or 0.
   - Read the provided code to deduce exactly what this field represents. 
   - Example: If the code implies the field is a URL, return "https://example.com". If it is an email, return "user@example.com". If it is a temperature threshold, return 75.5.

3. Execution Readiness:
   - The generated value MUST be logically sound so the provided code can execute it immediately without throwing validation or logical errors."""
            },
            {
                "role": "user",
                "content": f"""Please generate the safest, most realistic default value for this specific field.

### FIELD SCHEMA:
```json
{json.dumps(field_schema, indent=2)}
{code}
```"""
            }
        ],
        text_format=DefaultValue
    )

    return response.output_parsed.value


# 🔥 New AI function to generate the event name
# 🔥 Updated AI function to generate the event name based on the default values
def generate_event_name(code: str, schema: list) -> str:
    response = client.responses.parse(
        model="gpt-5-chat-latest",
        input=[
            {
                "role": "system",
                "content": """You are an Expert API QA Engineer. 
Your task is to generate a short, highly descriptive, and human-readable name for a default test payload.

CRITICAL INSTRUCTION: 
Analyze the "default" values provided in the schema context. The name MUST directly reflect the specific data values injected into this test case.

RULES:
1. MUST be under 5 words.
2. MUST use Title Case.
3. Examples based on data: If defaults are [25, 30] for temperature, name it "Standard Temperature Array". If default is "user@test.com", name it "Valid User Email Payload".
4. DO NOT use special characters, underscores, or hyphens."""
            },
            {
                "role": "user",
                # Using indent=2 makes it much easier for the AI to spot the "default" keys
                "content": f"Code Context:\n{code}\n\nSchema (containing the generated default values):\n{json.dumps(schema, indent=2)}"
            }
        ],
        text_format=EventName
    )

    return response.output_parsed.name


# =========================
# 🔁 INJECT DEFAULTS
# =========================

def inject_defaults(schema: list, code: str):
    for field in schema:
        if field.get("input") == "object":
            continue

        try:
            default_value = generate_default_for_field(code, field)

            field["default"] = default_value
            field["multiple"] = False

        except Exception as e:
            print(f"⚠️ Default generation failed for {field.get('key')}: {e}")

    return schema


# =========================
# 🔌 MAIN FUNCTION
# =========================

def update_default_event_with_existing_files(function_slug: str, code: str):
    token = os.getenv("BEARER_TOKEN")
    org_id = os.getenv("ORG_ID")
    headers = {
        "X-Organization-ID": org_id,
        "Authorization": f"Bearer {token}"
    }

    # -------------------------
    # STEP 1: GET FILES
    # -------------------------
    details_url = f"https://cortexone.rival.io/api/v1/function/agent-foundry/{function_slug}/details"

    details_res = requests.get(details_url, headers=headers).json()

    files = details_res["data"]["versions"][0]["files"]

    files_payload = {
        "files": [
            {
                "filename": file["meta"]["name"],
                "content": file["data"]
            }
            for file in files
        ]
    }

    # -------------------------
    # STEP 2: GENERATE SCHEMA
    # -------------------------
    schema_url = "https://cortexone.rival.io/api/app/generate-schema"

    schema_res = requests.post(
        schema_url,
        headers={**headers, "Content-Type": "application/json"},
        data=json.dumps(files_payload)
    ).json()

    schema = schema_res.get("schema", [])

    # 🔥 Inject defaults using AI
    schema = inject_defaults(schema, code)

    # 🔥 Generate meaningful event name
    generated_event_name = generate_event_name(code, schema)
    print(f"\n🧠 AI Generated Event Name: '{generated_event_name}'")

    # -------------------------
    # STEP 3: GET DEFAULT EVENT
    # -------------------------
    events_url = f"https://cortexone.rival.io/api/v1/functions/agent-foundry/{function_slug}/events"

    events_res = requests.get(events_url, headers=headers).json()

    default_event_id = None

    for event in events_res.get("data", []):
        if event.get("event_name") == "default":
            default_event_id = event["id"]
            break

    if not default_event_id:
        raise Exception("❌ Default event not found")

    # -------------------------
    # STEP 4: UPDATE EVENT
    # -------------------------
    update_payload = {
        "event_name": generated_event_name,  # 🔥 Using the AI generated name here!
        "event_data": {
            "type": "body",
            "schema": schema
        }
    }

    update_url = f"https://cortexone.rival.io/api/v1/events/{default_event_id}"

    update_res = requests.put(
        update_url,
        headers={**headers, "Content-Type": "application/json"},
        data=json.dumps(update_payload)
    )

    print("\n✅ Default Event Updated:")
    print(json.dumps(update_res.json(), indent=2))

    return update_res.json()


# =========================
# 🧪 TEST
# =========================

if __name__ == "__main__":
    sample_code = """
def sum_numbers(num):
    return sum(num)
"""

    update_default_event_with_existing_files(
        function_slug="your-function-slug",
        code=sample_code
    )