from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List, Union
from openai import OpenAI
import os
import requests

# =========================
# 🔐 ENV
# =========================
load_dotenv()

client = OpenAI()

# =========================
# 🧠 STRUCTURED MODELS (RECURSIVE)
# =========================

# Forward declaration for recursive types
class ObjectNode(BaseModel):
    # An object is just a list of KeyValue pairs
    properties: List['KeyValue']

class KeyValue(BaseModel):
    key: str
    # Value can be a primitive, a list of primitives, a nested ObjectNode, or a list of ObjectNodes
    value: Union[
        str, 
        int, 
        float, 
        bool, 
        List[str], 
        List[int], 
        List[float], 
        ObjectNode, 
        List[ObjectNode]
    ]

# Required by Pydantic to resolve the recursive references
ObjectNode.model_rebuild()

class TestCase(BaseModel):
    event_name: str
    event_data: List[KeyValue]

class TestCases(BaseModel):
    cases: List[TestCase] = Field(..., min_length=3, max_length=5)


# =========================
# 🧠 AI GENERATION
# =========================
def generate_test_cases(code: str) -> List[TestCase]:
    response = client.responses.parse(
        model="gpt-5-chat-latest",
        input=[
            {
                "role": "system",
                "content": """You are an Expert QA Engineer and Software Developer. 
Your task is to analyze the provided code, identify its expected input parameters, and generate BETWEEN 3 AND 5 distinct, realistic test cases (inclusive). Never return fewer than 3 or more than 5 cases. Cover a mix of: happy path, edge cases, boundary values, and invalid or partial inputs where the code defines explicit error handling.

CRITICAL RULES FOR OUTPUT FIELDS:

1. event_name: 
   - MUST be a short, human-readable description of the test scenario (e.g., "Standard Valid Payload", "Edge Case - Missing Optional Fields").

2. event_data: 
   - MUST be a list of key-value pairs representing the input payload.
   - The 'keys' MUST strictly match the exact variable, payload, or parameter names the code expects. Do not invent arbitrary keys.
   - For complex nested dictionaries, use the `ObjectNode` structure (which is simply a nested list of 'properties').
   - For lists of dictionaries, return a list of `ObjectNode` structures.
   - The 'values' MUST be realistic, valid data types that the code can successfully process."""
            },
            {
                "role": "user",
                "content": f"""Please analyze this code and generate 3 to 5 test cases as specified.

### CODE TO ANALYZE:
```python
{code}
```"""
            }
        ],
        text_format=TestCases
    )

    return response.output_parsed.cases


# =========================
# 🔁 HELPER: RECURSIVE DICT CONVERTER
# =========================

def unpack_value(val):
    """Recursively unpacks ObjectNodes and Lists into standard Python dicts/lists."""
    if isinstance(val, ObjectNode):
        return {item.key: unpack_value(item.value) for item in val.properties}
    elif isinstance(val, list):
        return [unpack_value(item) for item in val]
    else:
        return val

def convert_to_dict(event_data_list: List[KeyValue]) -> dict:
    """Entry point to convert the top-level List[KeyValue] into a dict."""
    return {item.key: unpack_value(item.value) for item in event_data_list}


# =========================
# 🔌 API CALL
# =========================

def create_event(function_id: str, event_name: str, event_data: dict):
    token = os.getenv("BEARER_TOKEN")
    org_id = os.getenv("ORG_ID")
    url = "https://cortexone.rival.io/api/v1/events"

    payload = {
        "event_name": event_name,
        "function_id": function_id,
        "event_data": event_data
    }

    headers = {
        "X-Organization-ID": org_id,
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, json=payload)
    return response.json()


# =========================
# 🚀 MAIN ENTRY (FOR AGENT)
# =========================

def create_test_cases_for_function(function_id: str, code: str):
    cases = generate_test_cases(code)

    results = []

    for case in cases:
        # Recursively converts the complex Pydantic objects into standard dictionaries
        event_data_dict = convert_to_dict(case.event_data)

        res = create_event(
            function_id=function_id,
            event_name=case.event_name,
            event_data=event_data_dict
        )

        results.append(res)

    return results


# =========================
# 🧪 LOCAL TEST
# =========================

if __name__ == "__main__":
    sample_code = """
def process_ledger(payload):
    # Expects payload to have 'ledger_entries' containing a list of dicts 
    # with 'transaction_id', 'debit_usd', and 'credit_usd'
    for entry in payload.get("ledger_entries", []):
        if entry["debit_usd"] != entry["credit_usd"]:
            return False
    return True
"""

    create_test_cases_for_function(
        function_id="e067f8a1-2626-42bd-a124-520e96c61580",
        code=sample_code
    )