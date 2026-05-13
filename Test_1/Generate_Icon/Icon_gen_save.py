from dotenv import load_dotenv
import os
import requests
import json
from openai import OpenAI
from pydantic import BaseModel

# =========================
# 🔐 ENV
# =========================
load_dotenv()


client = OpenAI()

# =========================
# 🧠 AI MODEL
# =========================

from typing import Literal

class IconChoice(BaseModel):
    index: Literal[0, 1, 2, 3, 4]


# =========================
# 🔁 BUILD PAYLOAD FROM DETAILS API
# =========================

def build_icon_payload(function_slug: str, headers: dict):


    details_url = f"https://cortexone.rival.io/api/v1/function/agent-foundry/{function_slug}/details"

    details_res = requests.get(details_url, headers=headers).json()

    data = details_res["data"]

    payload = {
        "type": "function",
        "function": {
            "additional_prompt": data["short_description"],
            "function_name": function_slug,
            "short_description": data["short_description"],
            "long_description": data.get("long_description", ""),
            "categories": [c["name"] for c in data.get("categories", [])],
            "tags": [t["name"] for t in data.get("tags", [])]
        }
    }

    return payload


# =========================
# 🧠 AI ICON SELECTION
# =========================

def select_best_icon(icons: list, context: str):
    
    # 🔥 STRIP OUT SVGs: Create a clean list of just the index and the style
    simplified_icons = [
        {"index": i, "style": icon["style"]} 
        for i, icon in enumerate(icons)
    ]

    response = client.responses.parse(
        model="gpt-5-chat-latest",
        input=[
            {
                "role": "system",
                "content": """
You are an expert UI/UX designer. Select the BEST icon style index for the given function.

Style Guidelines:
- "geometric": Best for math, analytics, data processing, and structured logic.
- "illustrative": Best for media, education, creative tools, and human-centric apps.
- "lettermark": Best for text generation, NLP, document parsing, and translation.
- "abstract": Best for AI, complex algorithms, cybersecurity, and backend systems.
- "symbolic": Best for general utilities, physical world actions, and standard developer tools.

Rules:
- Read the Function Context to understand what the tool does.
- Pick the style that semantically matches the function's purpose.
- Return ONLY the integer index of the best match.
"""
            },
            {
                "role": "user",
                "content": f"""
Function Context:
{context}

Available Icons:
{json.dumps(simplified_icons, indent=2)}
"""
            }
        ],
        text_format=IconChoice
    )

    return response.output_parsed.index

# =========================
# 🚀 MAIN FUNCTION
# =========================

def generate_and_upload_icon(function_id: str, function_slug: str):
    token = os.getenv("BEARER_TOKEN")
    org_id = os.getenv("ORG_ID")
    headers = {
        "X-Organization-ID": org_id,
        "Authorization": f"Bearer {token}"
    }

    # -------------------------
    # STEP 1: Build payload
    # -------------------------
    print("\n📦 Fetching function details...")
    payload = build_icon_payload(function_slug, headers)

    # -------------------------
    # STEP 2: Generate icons
    # -------------------------
    print("\n🎨 Generating icons...")
    gen_url = "https://cortexone.rival.io/api/v1/icons/generate"

    gen_res = requests.post(
        gen_url,
        headers={**headers, "Content-Type": "application/json"},
        json=payload
    ).json()

    icons = gen_res["data"]["icons"]

    # -------------------------
    # STEP 3: AI selects best
    # -------------------------
    print("\n🧠 Selecting best icon...")
    selected_index = select_best_icon(
        icons,
        payload["function"]["short_description"]
    )

    print(f"✅ Selected Icon Index: {selected_index}")

    selected_svg = icons[selected_index]["svg_content"]

    # Fix encoding
    selected_svg = selected_svg.encode().decode("unicode_escape")

    # -------------------------
    # STEP 4: Save SVG
    # -------------------------
    file_path = "generated-icon.svg"

    with open(file_path, "w") as f:
        f.write(selected_svg)

    # -------------------------
    # STEP 5: Upload icon
    # -------------------------
    print("\n🚀 Uploading icon...")

    upload_url = f"https://cortexone.rival.io/api/v1/functions/{function_id}/icon"

    with open(file_path, "rb") as f:
        files = {
            "file": ("generated-icon.svg", f, "image/svg+xml")
        }

        upload_res = requests.put(upload_url, headers=headers, files=files)

    print("\n🎉 Icon Upload Response:")
    print(json.dumps(upload_res.json(), indent=2))

    return upload_res.json()


# =========================
# 🧪 TEST
# =========================

if __name__ == "__main__":
    generate_and_upload_icon(
        function_id="16cb5efc-fce3-4f10-8b0b-aeb86843c28e",
        function_slug="cortexone_acoustic_analysis_handler"
    )












# from dotenv import load_dotenv
# import os

# load_dotenv()
# token = os.getenv("BEARER_TOKEN")
# org_id = os.getenv("ORG_ID")
# print(token)

# def generate_and_upload_icon(function_id: str, function_slug: str):

#     import requests
#     import json

#     headers = {
#         "X-Organization-ID": org_id,
#         "Authorization": f"Bearer {token}"
#     }

#     # STEP 1: Generate Icons
#     gen_url = "https://cortexone.rival.io/api/v1/icons/generate"

#     payload = json.dumps({
#         "type": "function",
#         "function": {
#             "additional_prompt": "awsdsadsaddaawsdsadsaddaawsdsadsaddaawsdsadsaddaawsdsadsaddaawsdsadsadda",
#             "function_name": function_slug,
#             "short_description": "awsdsadsaddaawsdsadsaddaawsdsadsaddaawsdsadsaddaawsdsadsaddaawsdsadsadda",
#             "long_description": "",
#             "categories": ["Audio & Speech"], #Need to remap
#             "tags": ["33testcheck", "3d"] #Need to remap
#         }
#     })

#     gen_res = requests.request("POST", gen_url, headers={**headers, "Content-Type": "application/json"}, data=payload).json()

#     icons = gen_res["data"]["icons"]

#     # STEP 2: Pick one icon (example: index 1)
#     selected_svg = icons[1]["svg_content"] # ❗️❗️❗️❗️ AI WILL DO IT

#     # Convert escaped unicode to proper SVG
#     selected_svg = selected_svg.encode().decode("unicode_escape")

#     # STEP 3: Save to temp file
#     file_path = "generated-icon.svg"
#     with open(file_path, "w") as f:
#         f.write(selected_svg)

#     # STEP 4: Upload icon
#     upload_url = f"https://cortexone.rival.io/api/v1/functions/{function_id}/icon"

#     files = {
#         "file": ("generated-icon.svg", open(file_path, "rb"), "image/svg+xml")
#     }

#     upload_res = requests.request("PUT", upload_url, headers=headers, files=files)

#     return upload_res.json()


# if __name__ == "__main__":
#     print(generate_and_upload_icon(
#         function_id="53d8fb3a-60e5-4849-8aaa-b30625ada974",
#         function_slug="awsdsadsadda"
#     ))