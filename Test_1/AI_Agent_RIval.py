from openai import OpenAI
from pydantic import BaseModel
from typing import Any, Callable, Dict, List
import json

# 🔥 Added: Import the token manager
from token_auth import token_manager
from saving_metadata import save_metadata_to_excel
# 🔌 Import your APIs
from Function_Creation import function_name_check, check_tag_availability, tags_creation, tags_details, category_get, sector_get, function_creation

from Code_Requirements import save_function_version,add_environment_variable
from Function_Details import fetch_function_details
from Test_Case_Setting import update_default_event_with_existing_files,create_test_cases_for_function,delete_default_event
from Generate_Icon import generate_and_upload_icon
from Generate_Description import generate_and_save_description,auto_generate_complete_metadata
from Publish_Privately import release_function

client = OpenAI()


def is_auth_error(response: Any) -> bool:
    """Detect whether an API response indicates token/session expiry."""
    if not isinstance(response, dict):
        return False

    message = str(response.get("message", "")).lower()
    code = str(response.get("code", "")).lower()
    details = str(response.get("details", "")).lower()

    auth_keywords = ("unauthorized", "token", "expired", "jwt", "401", "forbidden")
    haystack = " ".join([message, code, details])
    return any(keyword in haystack for keyword in auth_keywords)


def guarded_api_call(call_name: str, func: Callable, *args, **kwargs):
    """
    Ensure token validity before each outbound call and retry once
    if the first response indicates auth/session expiry.
    """
    token_manager.ensure_valid_token()
    response = func(*args, **kwargs)

    if is_auth_error(response):
        print(f"⚠️ Auth issue detected during '{call_name}', refreshing token and retrying once...")
        token_manager.refresh()
        token_manager.ensure_valid_token()
        response = func(*args, **kwargs)

    return response

# =========================
# 🧠 SCHEMAS
# =========================

class FunctionMetadata(BaseModel):
    function_name: str
    short_description: str
    category_name: str
    sector_name: str
    tags: List[str]


class FunctionName(BaseModel):
    function_name: str


# =========================
# 🧠 AI GENERATION
# =========================

def generate_metadata(code, categories, sectors):
    response = client.responses.parse(
        model="gpt-5-chat-latest",
        input=[
            {
                "role": "system",
                "content": """You are an expert Technical Product Manager and Code Analyzer. 
Your task is to analyze code and generate precise, user-friendly metadata.

CRITICAL RULES FOR METADATA FIELDS:

1. function_name: 
   - MUST be a human-readable phrase, like a premium product name.
   - MUST use Title Case (e.g., "Home Theater Acoustic Analyzer", "Budget Expense Tracker").
   - STRICTLY PROHIBITED: Hyphens (-), underscores (_), or any special symbols.
   - STRICTLY PROHIBITED: Slug-style formatting (e.g., "home-theater-analyzer" ❌).
   - STRICTLY PROHIBITED: Prefixes like "cortexone".

2. short_description: 
   - Write a concise, action-oriented summary of what the script achieves.

3. category_name & sector_name: 
   - MUST be an EXACT match from the provided JSON lists. Do not invent or modify names.

4. tags: 
   - Generate EXACTLY 3 highly relevant tags (plain text, lowercase)."""
            },
            {
                "role": "user",
                "content": f"""Please analyze the following code and select the most appropriate category and sector.

### AVAILABLE CATEGORIES:
{json.dumps(categories, indent=2)}

### AVAILABLE SECTORS:
{json.dumps(sectors, indent=2)}

### CODE TO ANALYZE:
```python
{code}
```"""
            }
        ],
        text_format=FunctionMetadata
    )

    return response.output_parsed


# =========================
# 🔁 FUNCTION NAME VALIDATION
# =========================

def validate_function_name(name, code):
    for _ in range(5):
        res = guarded_api_call("function_name_check", function_name_check, name)
        print(f"🔍 API Response for '{name}': {res}")
        if res["data"]["available"]:
            return name

        print(f"❌ Name '{name}' exists. Regenerating...")

        response = client.responses.parse(
            model="gpt-5-chat-latest",
            input=[
                {
                "role": "system",
                "content": """
            Generate a unique, human-friendly function name.

            STRICT RULES:
            - Output must be plain English words ONLY
            - Use Title Case (each word capitalized)
            - DO NOT use hyphens (-), underscores (_), or any symbols
            - DO NOT include any prefixes like "cortexone"
            - DO NOT return slug-style names
            - Return a clean, readable phrase like a product name

            Examples of CORRECT output:
            - Home Theater Acoustic Analyzer
            - Budget Expense Tracker
            - Image Caption Generator

            Examples of WRONG output:
            - home-theater-analyzer ❌
            - cortexone-audio-tool ❌
            - audio_tool ❌
            """
            },
                            {
                    "role": "user",
                    "content": f"""
        Code:
        {code}

        Previous name '{name}' already exists.
        Generate a better, unique name.
        """
                }
            ],
            text_format=FunctionName
        )

        name = response.output_parsed.function_name

    raise Exception("Failed to generate unique function name")


# =========================
# 🔁 CATEGORY + SECTOR MAPPING
# =========================

def map_category(name, categories):
    for c in categories["categories"]:
        if c["name"].lower() == name.lower():
            return c["category_id"]
    raise Exception(f"Category '{name}' not found")


def map_sector(name, sectors):
    for s in sectors["sectors"]:
        if s["name"].lower() == name.lower():
            return s["sector_id"]
    raise Exception(f"Sector '{name}' not found")


# =========================
# 🔁 TAG HANDLING
# =========================

def process_tags(tags):
    tag_ids = []

    for tag in tags:
        print(f"\n🔎 Processing tag: {tag}")

        res = guarded_api_call("check_tag_availability", check_tag_availability, tag)

        # ✅ Available → create
        if res.get("message") == "Tag availability checked":
            created = guarded_api_call("tags_creation", tags_creation, tag)
            tag_ids.append(created["data"][0]["tag_id"])

        # ❌ Conflict → fetch existing
        elif res.get("message") == "Tag conflict":
            details = guarded_api_call("tags_details", tags_details)

            found = False
            for t in details["data"]["tags"]:
                if t["name"].lower() == tag.lower():
                    tag_ids.append(t["tag_id"])
                    found = True
                    break

            if not found:
                raise Exception(f"Tag '{tag}' conflict but not found in details")

    return ",".join(tag_ids)


def build_function_payload(function_name: str, metadata: FunctionMetadata, category_id: str, sector_id: str, tag_ids: str) -> Dict[str, str]:
    """Build the final function creation payload in one place."""
    return {
        "function_name": function_name,
        "short_description": metadata.short_description,
        "runtime": "python:3.13",
        "type": "function",
        "category_ids": category_id,
        "sector_ids": sector_id,
        "compute_type": "CPU",
        "tag_ids": tag_ids,
    }


def needs_openai_env(code: str) -> bool:
    return "openai" in code.lower()




# =========================
# 🚀 MAIN AGENT
# =========================

def run_agent(code):
    # Ensure token is valid at start; individual API calls are also guarded.
    token_manager.ensure_valid_token()

# ==========================
# Function Creating START
# ==========================
    print("\n🚀 Fetching categories & sectors...")
    categories = guarded_api_call("category_get", category_get)
    sectors = guarded_api_call("sector_get", sector_get)

    print("\n🧠 Generating metadata...")
    metadata = generate_metadata(code, categories, sectors)

    print("\nGenerated Metadata:", metadata)

    # 🔁 Validate function name
    print("\n🔁 Validating function name...")
    function_name = validate_function_name(metadata.function_name,code)
    print("\n📊 Saving to local Excel tracker...")
    save_metadata_to_excel(function_name, metadata)
    # 🔁 Map IDs
    print("\n🔁 Mapping category & sector...")
    category_id = map_category(metadata.category_name, categories)
    sector_id = map_sector(metadata.sector_name, sectors)

    # 🔁 Process tags
    print("\n🔁 Processing tags...")
    tag_ids = process_tags(metadata.tags)

    # =========================
    # 🧾 FINAL PAYLOAD
    # =========================

    payload = build_function_payload(function_name, metadata, category_id, sector_id, tag_ids)

    print("\n✅ FINAL PAYLOAD:\n", payload)

    # 🔥 CALL FINAL API
    print("\n🚀 Creating function...")
    response = guarded_api_call("function_creation", function_creation, payload)

    print("\n🎉 RESPONSE:", json.dumps(response,indent=2))
    function_id = response["data"]["function"]["function_id"]
    function_slug=response["data"]["function_slug"]
    function_name=response["data"]["function"]["function_name"]
    
    
  
    print("\n✅ Function Created:", function_id)

# ==========================
# Function Creating ENDS
# ==========================
    
    
    
    
    
    
    
# =================================
# Function Details Fetch START
# ================================

    # response=fetch_function_details(function_slug) # NO need
    
# ================================
#  Function Details Fetch END
# ================================





# =====================================
# Function Code and Requirements START
# =====================================

    guarded_api_call("save_function_version", save_function_version, function_id, code)
    
# =====================================
# Function Code and Requirements END
# =====================================




# =====================================
# Environment Variable Setting Start
# =====================================

    if needs_openai_env(code):
        print("\n🌱 Adding OpenAI environment variable...")
        guarded_api_call("add_environment_variable", add_environment_variable, function_slug, "Openai_Key")
    else:
        print("\n⏭️ Skipping environment variable (OpenAI not used)")


# =====================================
# Environment Variable Setting Ends
# =====================================







# # =====================================
# # Default Schema + Default Values START
# # =====================================

#     print("\n🧠 Generating schema + injecting default values...")
#     update_default_event_with_existing_files(function_slug, code) # MAIN
#     # update_default_event_with_existing_files("cortexone-acoustic-analysis-handler", code) # Temporary

# # =====================================
# # Default Schema + Default Values END
# # =====================================






# =====================================
# Test Case Creation START
# =====================================

    print("\n🧪 Generating and creating test cases...")
    guarded_api_call("create_test_cases_for_function", create_test_cases_for_function, function_id, code)
    # create_test_cases_for_function("16cb5efc-fce3-4f10-8b0b-aeb86843c28e", code) # Temporary

# =====================================
# Test Case Creation END
# =====================================


# =====================================
# Default Test Form Deletion START
# =====================================

    print("\n🧠 Deleting default test form...")
    guarded_api_call("delete_default_event", delete_default_event, function_slug, function_id)
    # delete_default_event("cortexone-acoustic-analysis-handler", "16cb5efc-fce3-4f10-8b0b-aeb86843c28e") # Temporary

# =====================================
# Default Test Form Deletion END
# =====================================


# =====================================
# Generate Icon and save START
# =====================================
    print("\n🟢 Generating and saving icons...")
    guarded_api_call("generate_and_upload_icon", generate_and_upload_icon, function_id, function_slug)
    # generate_and_upload_icon("16cb5efc-fce3-4f10-8b0b-aeb86843c28e", "cortexone-acoustic-analysis-handler") # Temporary
    
# =====================================
# Generate Icon and save ENDS
# =====================================





# =====================================
# Generate Complete Metadata STARTS
# =====================================

    print("\n🧠 Generating complete metadata...")

    metadata_response = guarded_api_call("auto_generate_complete_metadata", auto_generate_complete_metadata, function_slug)

    print(json.dumps(metadata_response, indent=2))

    generated_changelog = metadata_response["generated_changelog"]
    # auto_generate_complete_metadata("cortexone-acoustic-analysis-handler") # Temporary 

# =====================================
# Generate Complete Metadata ENDS
# =====================================




# # =====================================
# # Generate Description STARTS
# # =====================================

#     print("\n📝 Generating and saving description...")
#     generate_and_save_description(function_name,function_slug, function_id) # MAIN
#     # generate_and_save_description("cortexone-acoustic-analysis-handler", "16cb5efc-fce3-4f10-8b0b-aeb86843c28e") # Temporary
    
# # =====================================
# # Generate Description ENDS
# # =====================================



# =====================================
# Publishing Function Privately Starts
# =====================================
    print("\n𝌚 Releasing Function")

    release_response = guarded_api_call(
        "release_function",
        release_function,
        function_slug,
        function_id,
        generated_changelog,
    )

    print(
        json.dumps(
            release_response,
            indent=2
        )
    )
    # release_function("cortexone-acoustic-analysis-handler-1", "16cb5efc-fce3-4f10-8b0b-aeb86843c28e") # Temporary
# =====================================
# Publishing Function Privately Ends
# =====================================

    return {
        "function_id": function_id,
        "function_slug": function_slug,
        "function_name": function_name,
        "release_response": release_response,
    }






# =========================
# 🧪 TEST
# =========================

if __name__ == "__main__":
  file_path = "/Users/amartyaghosh/Downloads/CortexOne/A-March/26-03-2026/Baby_Sleep_Regression.py"

  with open(file_path, "r") as f:
      code = f.read()

  function_creation_response=run_agent(code)