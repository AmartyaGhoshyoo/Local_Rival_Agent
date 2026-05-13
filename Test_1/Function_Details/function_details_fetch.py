import requests
from dotenv import load_dotenv
import os
import re

load_dotenv()


def to_kebab_case(name):

    # lowercase
    name = name.lower()

    # replace underscores with space
    name = name.replace("_", " ")

    # replace non-alphanumeric with dash
    name = re.sub(r"[^a-z0-9]+", "-", name)

    # remove leading/trailing dashes
    return name.strip("-")


def fetch_function_details(function_name: str):
    token = os.getenv("BEARER_TOKEN")
    org_id = os.getenv("ORG_ID")

    url = f"https://cortexone.rival.io/api/v1/function/agent-foundry/{function_name}/details"

    headers = {"X-Organization-ID": org_id, "Authorization": f"Bearer {token}"}

    response = requests.request("GET", url, headers=headers)
    import json

    print(json.dumps(response.json(), indent=2))
    return response.json()


if __name__ == "__main__":
    import json

    data = fetch_function_details("cortexone-acoustic-analysis-handler-1")


"""

{
  "success": true,
  "message": "Tool details loaded successfully",
  "data": {
    "function_id": "16cb5efc-fce3-4f10-8b0b-aeb86843c28e",
    "organization_id": "2b227103-7a6a-4430-8370-e70a3f6bb1f0",
    "function_name": "cortexone_acoustic_analysis_handler",
    "short_description": "Analyzes home theater room dimensions using physics-based acoustic modeling and AI synthesis to generate resonant frequency insights and subwoofer placement recommendations.",
    "long_description": "",
    "license": "",
    "video_demo_url": "",
    "readme": "",
    "example": "",
    "categories": [
      {
        "category_id": "b04a27d5-61d9-4b69-bc89-b0526f981193",
        "name": "AI & ML",
        "description": "",
        "functions_count": 0
      }
    ],
    "tags": [
      {
        "tag_id": "dd406b54-300e-460d-b2db-f93b151abe3e",
        "name": "acoustic-analysis",
        "created_at": "0001-01-01T00:00:00Z"
      },
      {
        "tag_id": "485d9fe5-1873-4e24-a1a6-fe21c941fe15",
        "name": "ai-agent",
        "created_at": "0001-01-01T00:00:00Z"
      },
      {
        "tag_id": "407d613a-226a-455e-8cd8-a8a72cded25f",
        "name": "resonance-modeling",
        "created_at": "0001-01-01T00:00:00Z"
      }
    ],
    "is_favorite": false,
    "visibility": "private",
    "organization_name": "Agent Foundry",
    "created_at": "2026-04-04T08:38:41.682847Z",
    "updated_at": "2026-04-04T11:02:09.54677Z",
    "versions": [
      {
        "version": "Draft",
        "runtime": "python:3.13",
        "compute_type": "CPU",
        "max_memory": 128,
        "max_runtime": 300,
        "cpu_limit": 2,
        "handler": "cortexone_function.cortexone_handler",
        "files": [
          {
            "path": "/cortexone_function.py",
            "meta": {
              "name": "cortexone_function.py",
              "mime": "text/x-python"
            },
            "data": "import os\nimport json\nfrom typing import Any, Dict, List\nfrom pydantic import BaseModel, Field, ValidationError\nfrom openai import OpenAI\n\n# ==========================================\n# 1. Configuration & Hard Constraints\n# ==========================================\n# STRICT RULE: Rely entirely on system environment variables.\nOPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')\nclient = OpenAI(api_key=OPENAI_API_KEY)\n\n# Speed of sound in air at 68\u00b0F (20\u00b0C) is roughly 1130 feet per second.\nSPEED_OF_SOUND_FPS = 1130.0\n\n# ==========================================\n# 2. Data Models (Strict Input & Validation)\n# ==========================================\nclass HomeTheaterInput(BaseModel):\n    room_length_ft: float = Field(..., gt=0, description=\"The length of the room in feet.\")\n    room_width_ft: float = Field(..., gt=0, description=\"The width of the room in feet.\")\n    room_height_ft: float = Field(..., gt=0, description=\"The ceiling height in feet.\")\n\nclass AcousticValidationPlan(BaseModel):\n    is_valid_room_context: bool = Field(\n        description=\"False if the dimensions violate physical reality for a room (e.g., 0.1 ft or 5000 ft ceilings).\"\n    )\n\nclass AcousticInsight(BaseModel):\n    the_acoustic_audit: str = Field(description=\"High-level summary of the room's geometry and the primary resonant frequencies calculated.\")\n    the_physics_reality: str = Field(description=\"Scientific explanation of 'Room Modes' (standing waves). Explain how parallel walls cause specific low frequencies to trap themselves, creating massive peaks (boomy bass) and nulls (dead zones).\")\n    action_plan: str = Field(description=\"Strict Acoustical Engineer advice. Instruct the user exactly where to place their subwoofer to physically cancel out the worst standing wave (e.g., mid-wall placement to avoid exciting double modes in corners).\")\n\nclass AgentResponse(BaseModel):\n    room_dimensions_ft: str\n    axial_mode_length_hz: float\n    axial_mode_width_hz: float\n    axial_mode_height_hz: float\n    critical_overlaps_identified: List[str]\n    insight: AcousticInsight\n\n# ==========================================\n# 3. Tool: Deterministic Acoustic Physics Engine\n# ==========================================\nclass AcousticPhysicsTool:\n    def _validate_acoustic_logic(self, l: float, w: float, h: float) -> AcousticValidationPlan:\n        \"\"\"Step 1: AI Gatekeeper validates reality before running wave physics.\"\"\"\n        system_prompt = \"\"\"\n        You are an elite Acoustical Engineer.\n        1. Validate reality. If the dimensions represent a shoebox (1 ft x 1 ft) or a stadium (5000 ft), set is_valid_room_context to false.\n        \"\"\"\n        completion = client.beta.chat.completions.parse(\n            model=\"gpt-5-chat-latest\",\n            messages=[\n                {\"role\": \"system\", \"content\": system_prompt},\n                {\"role\": \"user\", \"content\": f\"Length: {l} | Width: {w} | Height: {h}\"}\n            ],\n            response_format=AcousticValidationPlan,\n            temperature=0.0 \n        )\n        return completion.choices[0].message.parsed\n\n    def execute_resonance_audit(self, input_data: HomeTheaterInput) -> Dict[str, Any]:\n        # 1. AI Gatekeeper Validation\n        plan = self._validate_acoustic_logic(\n            input_data.room_length_ft, \n            input_data.room_width_ft, \n            input_data.room_height_ft\n        )\n        \n        if not plan.is_valid_room_context:\n            return {\"error\": \"INVALID_ROOM_CONTEXT\"}\n\n        # 2. Native Python Pure Acoustic Mathematics (Axial Modes)\n        # Formula: Frequency = Speed of Sound / (2 * Dimension)\n        mode_l = SPEED_OF_SOUND_FPS / (2 * input_data.room_length_ft)\n        mode_w = SPEED_OF_SOUND_FPS / (2 * input_data.room_width_ft)\n        mode_h = SPEED_OF_SOUND_FPS / (2 * input_data.room_height_ft)\n        \n        # 3. Identify Critical Geometry Flaws (Overlapping Modes)\n        # If two modes are within 3 Hz of each other, they compound into a \"Double Mode\"\n        # If all three are close, it's a \"Triple Mode\" (Acoustic nightmare)\n        overlaps = []\n        if abs(mode_l - mode_w) <= 3.0:\n            overlaps.append(f\"SEVERE: Length and Width share a standing wave near {round((mode_l+mode_w)/2, 1)} Hz (Double Room Mode).\")\n        if abs(mode_l - mode_h) <= 3.0:\n            overlaps.append(f\"SEVERE: Length and Height share a standing wave near {round((mode_l+mode_h)/2, 1)} Hz.\")\n        if abs(mode_w - mode_h) <= 3.0:\n            overlaps.append(f\"SEVERE: Width and Height share a standing wave near {round((mode_w+mode_h)/2, 1)} Hz.\")\n            \n        if not overlaps:\n            overlaps.append(\"OPTIMAL: Frequencies are evenly distributed. No severe geometric doubling detected.\")\n\n        return {\n            \"l\": input_data.room_length_ft,\n            \"w\": input_data.room_width_ft,\n            \"h\": input_data.room_height_ft,\n            \"mode_l\": round(mode_l, 1),\n            \"mode_w\": round(mode_w, 1),\n            \"mode_h\": round(mode_h, 1),\n            \"overlaps\": overlaps\n        }\n\n# ==========================================\n# 4. Agent Logic (The Acoustical Engineer)\n# ==========================================\ndef synthesize_acoustic_report(telemetry: Dict[str, Any]) -> AcousticInsight:\n    system_prompt = \"\"\"\n    You are an elite Acoustical Engineer tuning a high-end home theater.\n    \n    RULE 1: THE MATHEMATICAL REALITY\n    Rely EXACTLY on the physics telemetry provided. Reference the exact Hz frequencies calculated.\n    \n    RULE 2: THE ACOUSTIC REALITY\n    Explain standing waves. Low-frequency soundwaves physically reflect off parallel walls. If the wavelength perfectly matches the room dimension, it traps itself. The corners become high-pressure zones (overwhelming, muddy bass), and the center of the room becomes a null (dead zone where bass disappears).\n    \n    RULE 3: THE ACTION PLAN\n    Provide a ruthless, uncompromising placement strategy. If there is a Double Mode, explicitly forbid corner subwoofer placement (which excites all modes simultaneously). Tell them to place the subwoofer at the midpoint of the front or side wall to physically cancel the standing wave.\n    \"\"\"\n\n    user_prompt = f\"\"\"\n    ACOUSTIC PHYSICS TELEMETRY:\n    - Dimensions: {telemetry['l']}'L x {telemetry['w']}'W x {telemetry['h']}'H\n    - Primary Length Resonance (Axial): {telemetry['mode_l']} Hz\n    - Primary Width Resonance (Axial): {telemetry['mode_w']} Hz\n    - Primary Height Resonance (Axial): {telemetry['mode_h']} Hz\n    - Critical Geometric Flaws Identified: {', '.join(telemetry['overlaps'])}\n    \"\"\"\n\n    try:\n        completion = client.beta.chat.completions.parse(\n            model=\"gpt-5-chat-latest\",\n            messages=[{\"role\": \"system\", \"content\": system_prompt}, {\"role\": \"user\", \"content\": user_prompt}],\n            response_format=AcousticInsight,\n            temperature=0.1 \n        )\n        return completion.choices[0].message.parsed\n    except Exception as e:\n        raise ValueError(f\"AI Synthesis Failed: {str(e)}\")\n\n# ==========================================\n# 5. Strict Handler Signature\n# ==========================================\ndef cortexone_handler(event: dict, context: Any = None) -> Dict[str, Any]:\n    try:\n        # Step 1: Schema Validation\n        input_data = HomeTheaterInput(**event)\n        \n        # Step 2: Live Mathematical Execution\n        tool = AcousticPhysicsTool()\n        telemetry = tool.execute_resonance_audit(input_data)\n        \n        # Gatekeeper Failures\n        if telemetry.get(\"error\") == \"INVALID_ROOM_CONTEXT\":\n            return {\"status\": \"error\", \"message\": \"ERROR: Input rejected. AI Gatekeeper determined the dimensions violate physical reality for a home theater room.\"}\n            \n        # Step 3: AI Synthesis\n        insight = synthesize_acoustic_report(telemetry)\n\n        return {\"status\": \"success\", \"data\": AgentResponse(\n            room_dimensions_ft=f\"{telemetry['l']}x{telemetry['w']}x{telemetry['h']}\",\n            axial_mode_length_hz=telemetry[\"mode_l\"],\n            axial_mode_width_hz=telemetry[\"mode_w\"],\n            axial_mode_height_hz=telemetry[\"mode_h\"],\n            critical_overlaps_identified=telemetry[\"overlaps\"],\n            insight=insight\n        ).model_dump()}\n\n    except ValidationError as e:\n        return {\"status\": \"error\", \"message\": f\"Input Schema Failure: {str(e)}\"}\n    except Exception as e:\n        return {\"status\": \"error\", \"message\": f\"System Error: {str(e)}\"}\n\n# ==========================================\n# 6. Execution Test Blocks\n# ==========================================\nif __name__ == \"__main__\":\n    print(\"--- Running The 'Home Theater' Resonant Frequency Finder (Pure Physics Architecture) ---\\n\")\n\n    # [Test 1: Positive Path - The Nightmare Square Room]\n    print(\"[Test 1: test_cortexone_square_room_double_mode]\")\n    event_1 = {\n        \"room_length_ft\": 15.0,\n        \"room_width_ft\": 15.0,\n        \"room_height_ft\": 8.0\n    }\n    print(json.dumps(cortexone_handler(event_1), indent=2))\n    print(\"\\n\")\n\n    # [Test 2: Positive Path - The \"Golden Ratio\" Acoustic Room]\n    print(\"[Test 2: test_cortexone_golden_ratio_optimal_modes]\")\n    event_2 = {\n        \"room_length_ft\": 23.0,\n        \"room_width_ft\": 16.0,\n        \"room_height_ft\": 10.0\n    }\n    print(json.dumps(cortexone_handler(event_2), indent=2))\n    print(\"\\n\")\n\n    # [Test 3: Negative Path - Semantic Gatekeeper Reality Check]\n    print(\"[Test 3: test_cortexone_invalid_room_dimensions]\")\n    event_3 = {\n        \"room_length_ft\": 0.5,\n        \"room_width_ft\": 5000.0,\n        \"room_height_ft\": 2.0\n    }\n    print(json.dumps(cortexone_handler(event_3), indent=2))\n    print(\"\\n\")"
          },
          {
            "path": "/requirements.txt",
            "meta": {
              "name": "requirements.txt",
              "mime": "text/plain"
            },
            "data": "pydantic\nopenai"
          }
        ],
        "environment": null,
        "state": "draft",
        "created_at": "2026-04-04T08:38:41.682847Z",
        "updated_at": "2026-04-04T10:29:12.690528Z",
        "event_id": "",
        "changelog": null,
        "event_name": "",
        "event_data": null,
        "events": [
          {
            "EventID": "a5583bb9-d1ec-47b2-aec3-fe6b7c7f553e",
            "EventName": "default",
            "EventData": {
              "type": "body",
              "schema": []
            }
          }
        ],
        "visibility": "private",
        "digital_asset_id": "",
        "is_deprecated": false,
        "days_left": null,
        "uses_digital_assets": false,
        "makes_external_calls": false
      }
    ],
    "summary": {
      "total_earnings": 0,
      "total_executions": 1,
      "rating": 0,
      "current_price": 0,
      "total_reviews": 0
    },
    "default_event": {
      "id": "a5583bb9-d1ec-47b2-aec3-fe6b7c7f553e",
      "event_name": "default",
      "event_data": {
        "schema": [],
        "type": "body"
      },
      "is_default": true,
      "created_at": "2026-04-04T08:38:41.682847Z",
      "updated_at": "2026-04-05T19:39:57.21729Z"
    },
    "icon_url": "",
    "total_favorites": 0,
    "organization_email": "agent.foundry@yahoo.com",
    "organization_profile_picture": "https://storage.googleapis.com/rival-data/organizations-Picture/1773288089082933898_cropped-logo.png",
    "can_review": false,
    "type": "function",
    "access_level": "editor",
    "is_deletable": false,
    "sectors": [
      {
        "sector_id": "800db3ed-f8db-4024-aeef-3d2edf4490a8",
        "name": "Data, AI & Analytics",
        "description": "Data platforms, machine learning, artificial intelligence, and business intelligence.",
        "slug": ""
      }
    ],
    "is_deprecated": false
  }
}

"""
