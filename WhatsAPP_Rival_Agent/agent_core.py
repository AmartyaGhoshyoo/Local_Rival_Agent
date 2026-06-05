from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List

from agents import Agent, Runner, function_tool
from cortexone_template import CORTEXONE_MINIMAL_EXAMPLE, CORTEXONE_SYSTEM_INSTRUCTIONS
from local_runner import run_cortexone_handler
from session import UserContext, get_user_context, get_agent_session

ROOT = Path(__file__).resolve().parent.parent

def _deploy_saved_code(code: str) -> str:
    """Run deploy_worker in a subprocess."""
    if not code or not code.strip():
        return "No saved code to deploy. Ask me to generate CortexOne code first."
        
    wa = Path(__file__).resolve().parent 
    
    # 🔥 FIX 1: Explicitly point to the OS's hidden temp directory so Uvicorn ignores it
    safe_temp_dir = tempfile.gettempdir()
    
    with tempfile.NamedTemporaryFile(
        mode="w", suffix="_deploy.py", delete=False, encoding="utf-8", dir=safe_temp_dir
    ) as f:
        f.write(code)
        path = f.name
    try:
        proc = subprocess.run(
            [sys.executable, str(wa / "deploy_worker.py"), path],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=3600,
            env=os.environ.copy(),
        )
        out = (proc.stdout or "").strip()
        err = (proc.stderr or "").strip()
        body = "\n".join(x for x in (out, err) if x)
        if proc.returncode != 0:
            return f"Deploy subprocess failed (exit {proc.returncode}):\n{body or '(no output)'}"
        return body or "(deploy finished successfully!)"
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


# =========================
# SDK TOOLS
# =========================

@function_tool
def save_cortexone_code(context: UserContext, python_source: str) -> str:
    """Save a complete Python file for CortexOne."""
    context.last_code = python_source
    print("Saved code to context.", context.last_code)
    return f"Saved handler source ({len(python_source)} chars). You can run tests or deploy when the user asks."

# 🔥 FIX 2: Added a new tool to retrieve the code!
@function_tool
def get_saved_cortexone_code(context: UserContext) -> str:
    """Call this ONLY when the user explicitly asks to see, view, or show the saved code."""
    if not context.last_code:
        print("No code has been saved yet.")
        return "No code has been saved yet."
    return context.last_code

@function_tool
def run_saved_code_locally(context: UserContext, events_json_string: str) -> str:
    """Run the last saved CortexOne handler locally. Returns stdout/stderr from execution."""
    if not context.last_code:
        return "No saved code. Generate code first (save_cortexone_code)."
    
    try:
        events = json.loads(events_json_string)
    except json.JSONDecodeError as e:
        return f"Failed to parse JSON. Please provide a valid JSON string. Error: {e}"

    if not isinstance(events, list) or not events:
        return "Provide a non-empty array of dicts."
        
    reports = []
    for i, ev in enumerate(events):
        if not isinstance(ev, dict):
            reports.append(f"Event {i}: skipped (not a dict)")
            continue
        reports.append(f"=== Event {i} ===\n{run_cortexone_handler(context.last_code, ev)}")
    return "\n\n".join(reports)

@function_tool
def deploy_saved_code_to_cortexone(context: UserContext) -> str:
    """Deploy the last saved handler. Only call when user asks to deploy/publish."""
    return _deploy_saved_code(context.last_code or "")


# =========================
# AGENT SETUP
# =========================

def _build_system_prompt() -> str:
    return f"""You are an advanced WhatsApp assistant for CortexOne function development.

Modes:
1) Casual chat — answer normally.
2) Write code — output a complete module and call `save_cortexone_code`.
3) Show code — call `get_saved_cortexone_code` and reply with the code in a ```python block.
4) Run locally — call `run_saved_code_locally` and pass `events_json_string`.
5) Deploy — call `deploy_saved_code_to_cortexone`.

CortexOne contract:
{CORTEXONE_SYSTEM_INSTRUCTIONS}

Minimal reference:
{CORTEXONE_MINIMAL_EXAMPLE}

Rules:
- Usually, prefer short WhatsApp-friendly summaries and avoid massive code blocks.
- HOWEVER, if the user explicitly asks to "show the code", "see the code", or "print the code", you MUST use `get_saved_cortexone_code` and send them the full code.
- If the user has not saved code yet, do not call run or deploy.
- If the user wants to search for, test, or interact with marketplace agents on rival.io, instruct them to simply type "search agent". Do not try to write code for marketplace searches yourself.
"""

agent = Agent(
    name="WhatsApp CortexOne Assistant",
    instructions=_build_system_prompt(),
    model='gpt-5-chat-latest',
    # 🔥 Added the new tool to the agent's brain!
    tools=[save_cortexone_code, get_saved_cortexone_code, run_saved_code_locally, deploy_saved_code_to_cortexone],
)


# =========================
# ASYNC EXECUTION RUNNER
# =========================

async def handle_user_message(user_text: str, sender_id: str) -> str:
    context = get_user_context(sender_id)
    session = get_agent_session(sender_id)
    result = await Runner.run(agent, user_text, context=context, session=session)
    return result.final_output


if __name__ == "__main__":
    import asyncio

    async def test_agent_flow():
        # Simulate a unique WhatsApp user ID
        test_sender_id = "test_user_999"

        print("==================================================")
        print("🧪 STARTING AGENT CORE TEST")
        print("==================================================")

        # ---------------------------------------------------------
        # TEST 1: Requesting code generation (Triggers save_cortexone_code)
        # ---------------------------------------------------------
        prompt_1 = "Write a CortexOne handler that adds two numbers, 'a' and 'b', from the event JSON."
        print(f"\n👤 User: {prompt_1}")
        print("🤖 AI is thinking...")
        
        response_1 = await handle_user_message(prompt_1, test_sender_id)
        
        print(f"✅ AI Response:\n{response_1}")
        
        # Verify the context memory directly to prove the tool worked silently
        ctx = get_user_context(test_sender_id)
        print(f"\n🔍 DIRECT MEMORY CHECK:")
        if ctx.last_code:
            print(f"   -> Successfully saved {len(ctx.last_code)} characters to UserContext!")
        else:
            print("   -> 🚨 ERROR: last_code is None. The save tool was not called.")

        print("\n--------------------------------------------------")

        # ---------------------------------------------------------
        # TEST 2: Requesting to view the code (Triggers get_saved_cortexone_code)
        # ---------------------------------------------------------
        prompt_2 = "Show me the code you just wrote."
        print(f"\n👤 User: {prompt_2}")
        print("🤖 AI is thinking...")
        
        response_2 = await handle_user_message(prompt_2, test_sender_id)
        
        print(f"✅ AI Response:\n{response_2}")

        print("\n==================================================")
        print("🏁 TEST COMPLETE")
        print("==================================================")

    # Run the async test loop
    asyncio.run(test_agent_flow())