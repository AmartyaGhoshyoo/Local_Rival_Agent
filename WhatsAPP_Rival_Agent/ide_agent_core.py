from __future__ import annotations

import json
import time
from pydantic import BaseModel, Field
from typing import Any, Optional

from agents import Agent, Runner, function_tool
from session import UserContext, get_user_context, get_agent_session
from cortexone_template import CORTEXONE_SYSTEM_INSTRUCTIONS, CORTEXONE_MINIMAL_EXAMPLE

import sys
from pathlib import Path

# 1. Find the root of your entire project (the folder holding everything)
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent

# 2. Target the exact folder where your API scripts live
LOCAL_DEPLOYMENT_DIR = ROOT_DIR / "Local_Rival_Deployment"

# 3. Inject it into Python's system path!
sys.path.insert(0, str(LOCAL_DEPLOYMENT_DIR))

# ==========================================
# 🔥 NOW YOUR IMPORTS WILL WORK GLOBALLY!
# ==========================================
from AI_Agent_RIval import (
    guarded_api_call, generate_metadata, validate_function_name, 
    map_category, map_sector, process_tags, build_function_payload, needs_openai_env
)
from Function_Creation import category_get, sector_get, function_creation
from Code_Requirements import save_function_version, add_environment_variable
from Test_Case_Setting import create_test_cases_for_function, delete_default_event
from Generate_Icon import generate_and_upload_icon
from Generate_Description import auto_generate_complete_metadata
from Publish_Privately import release_function
from Test_Case_Running import invoke_all_non_default_events

# ... (the rest of your ide_agent_core.py code continues here) ...
# =========================
# 🔥 PYDANTIC UI SCHEMA
# =========================
class IDEResponse(BaseModel):
    reply: str
    new_code: Optional[str] = None
    ui_state: str = Field(description="Must be one of: 'normal', 'show_run_button', 'show_deploy_button'")
    raw_api_data: Optional[str] = Field(description="Raw JSON string from API to display directly to user")

# =========================
# 🛠️ WORKFLOW TOOLS
# =========================
IDE_STATE = {
    "function_id": None,
    "function_slug": None
}
@function_tool
def phase_1_create_and_test(context: UserContext, code: str) -> str:
    print("Time at phase 1",time.time())
    categories = guarded_api_call("category_get", category_get)
    sectors = guarded_api_call("sector_get", sector_get)
    metadata = generate_metadata(code, categories, sectors)
    function_name = validate_function_name(metadata.function_name, code)
    
    category_id = map_category(metadata.category_name, categories)
    sector_id = map_sector(metadata.sector_name, sectors)
    tag_ids = process_tags(metadata.tags)

    payload = build_function_payload(function_name, metadata, category_id, sector_id, tag_ids)
    response = guarded_api_call("function_creation", function_creation, payload)
    
    # 🔥 FIX: Save to global dictionary instead of context copy
    global IDE_STATE
    IDE_STATE["function_id"] = response["data"]["function"]["function_id"]
    IDE_STATE["function_slug"] = response["data"]["function_slug"]
    print(f"💾 Phase 1 Saved ID to Global State: {IDE_STATE['function_id']}")
    
    guarded_api_call("save_function_version", save_function_version, IDE_STATE["function_id"], code)
    if needs_openai_env(code):
        guarded_api_call("add_environment_variable", add_environment_variable, IDE_STATE["function_slug"], "Openai_Key")

    generated_tests = guarded_api_call("create_test_cases_for_function", create_test_cases_for_function, IDE_STATE["function_id"], code)
    guarded_api_call("delete_default_event", delete_default_event, IDE_STATE["function_slug"], IDE_STATE["function_id"])

    return f"TEST_CASES_JSON:{json.dumps(generated_tests)}"
@function_tool
def phase_2_invoke_tests(context: UserContext) -> str:
    global IDE_STATE
    func_id = IDE_STATE["function_id"]
    func_slug = IDE_STATE["function_slug"]
    
    print(f"📖 Phase 2 Reading from Global State: {func_id}")
    
    if not func_id:
        return "Error: No function ID found. Create tests first."
    
    results = invoke_all_non_default_events(func_slug, func_id)
    return f"RAW_RESULTS:{json.dumps(results)}"

@function_tool
def phase_3_deploy_function(context: UserContext) -> str:
    global IDE_STATE
    func_id = IDE_STATE["function_id"]
    func_slug = IDE_STATE["function_slug"]

    if not func_id:
        return "Error: No function ID found."

    guarded_api_call("generate_and_upload_icon", generate_and_upload_icon, func_id, func_slug)
    metadata_response = guarded_api_call("auto_generate_complete_metadata", auto_generate_complete_metadata, func_slug)
    generated_changelog = metadata_response["generated_changelog"]
    
    guarded_api_call("release_function", release_function, func_slug, func_id, generated_changelog)
    return "Deployment complete!"

# =========================
# 🧠 AGENT INSTRUCTIONS
# =========================
def _build_ide_system_prompt() -> str:
    return """You are a strictly structured IDE workflow agent. You execute background APIs for the user and assist with local code editing.

CRITICAL WORKFLOW RULES - YOU MUST USE THE TOOLS:
1. If the user asks to "create test cases", YOU MUST CALL THE TOOL `phase_1_create_and_test`. Pass the Current Code as the argument. Extract the JSON from the tool's return value, place it EXACTLY into the `raw_api_data` field, set `ui_state` to 'show_run_button', and YOUR `reply` TEXT MUST BE EXACTLY AND ONLY: "Test cases generated successfully! Click the button below to run them."
2. If the user asks to "Run the test cases", YOU MUST CALL THE TOOL `phase_2_invoke_tests`. Extract the JSON from the tool's return value, place it EXACTLY into the `raw_api_data` field, set `ui_state` to 'show_deploy_button', and YOUR `reply` TEXT MUST BE EXACTLY AND ONLY: "Test run complete! Here are the results:"
3. If the user asks to "Deploy", YOU MUST CALL THE TOOL `phase_3_deploy_function`. Set `ui_state` to 'normal' and reply with success.

GENERAL CODE MODIFICATION RULES:
4. If the user asks you to modify, add, or fix something in their current file (e.g., "add another test case to the end"), you must take the existing code, insert the changes, and populate the `new_code` field with the COMPLETE, REWRITTEN FILE from top to bottom.
⚠️ WARNING: NEVER return just a code snippet or just the newly added lines inside the `new_code` field. If you provide a partial snippet, it will erase the user's entire file. For general coding tasks, set `ui_state` to 'normal'.
"""

ide_agent = Agent(
    name="VS Code CortexOne Assistant",
    instructions=_build_ide_system_prompt(),
    tools=[phase_1_create_and_test, phase_2_invoke_tests, phase_3_deploy_function],
    output_type=IDEResponse,
)

async def handle_ide_message(user_text: str, sender_id: str) -> Any:
    context = get_user_context(sender_id)
    session = get_agent_session(sender_id)
    print("Time at calling agent",time.time())
    result = await Runner.run(ide_agent, user_text, context=context, session=session)
    print("Time at returning agent",time.time())
    return result.final_output