from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

# 🔥 Import BaseModel and Optional for our structured output
from pydantic import BaseModel

from agents import Agent, Runner, function_tool
from local_runner import run_cortexone_handler
from session import UserContext, get_user_context, get_agent_session
from cortexone_template import CORTEXONE_SYSTEM_INSTRUCTIONS, CORTEXONE_MINIMAL_EXAMPLE

ROOT = Path(__file__).resolve().parent.parent

# =========================
# 🔥 PYDANTIC OUTPUT SCHEMA
# =========================
class IDEResponse(BaseModel):
    reply: str
    new_code: Optional[str] = None

# ... (Keep your _deploy_ide_code, run_current_code_locally, and deploy_current_code_to_cortexone functions exactly the same) ...

def _deploy_ide_code(code: str) -> str:
    if not code or not code.strip():
        return "No code provided to deploy."
    wa = Path(__file__).resolve().parent 
    safe_temp_dir = tempfile.gettempdir()
    with tempfile.NamedTemporaryFile(mode="w", suffix="_deploy.py", delete=False, encoding="utf-8", dir=safe_temp_dir) as f:
        f.write(code)
        path = f.name
    try:
        proc = subprocess.run([sys.executable, str(wa / "deploy_worker.py"), path], cwd=str(ROOT), capture_output=True, text=True, timeout=3600, env=os.environ.copy())
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

@function_tool
def run_current_code_locally(context: UserContext, python_code: str, events_json_string: str) -> str:
    try:
        events = json.loads(events_json_string)
    except json.JSONDecodeError as e:
        return f"Failed to parse JSON. Error: {e}"
    if not isinstance(events, list) or not events:
        return "Provide a non-empty array of dicts."
    reports = []
    for i, ev in enumerate(events):
        if not isinstance(ev, dict):
            reports.append(f"Event {i}: skipped (not a dict)")
            continue
        reports.append(f"=== Event {i} ===\n{run_cortexone_handler(python_code, ev)}")
    return "\n\n".join(reports)

@function_tool
def deploy_current_code_to_cortexone(context: UserContext, python_code: str) -> str:
    return _deploy_ide_code(python_code)

# =========================
# IDE AGENT SETUP
# =========================

def _build_ide_system_prompt() -> str:
    return f"""You are an elite AI pair programmer integrated directly inside the user's VS Code IDE.
You are helping the user write, test, and deploy CortexOne functions.

CortexOne Framework Rules:
{CORTEXONE_SYSTEM_INSTRUCTIONS}

Minimal CortexOne Template:
{CORTEXONE_MINIMAL_EXAMPLE}

YOUR CRITICAL INSTRUCTIONS:
1. NEVER ASK FOR PERMISSION TO WRITE CODE. If the user asks you to add, edit, or fix something, IMMEDIATELY rewrite the entire code and populate the `new_code` field in your JSON response. Do not say "If you want, I can update the file..." — just do it instantly.
2. If the user asks to DEPLOY the code, call `deploy_current_code_to_cortexone`.
3. If the user asks to TEST the code, call `run_current_code_locally`.
4. If you modify the code, you MUST output the COMPLETE rewritten file in the `new_code` field.
"""

ide_agent = Agent(
    name="VS Code CortexOne Assistant",
    instructions=_build_ide_system_prompt(),
    tools=[run_current_code_locally, deploy_current_code_to_cortexone],
    output_type=IDEResponse,  # 🔥 Tell the framework to enforce our Pydantic model
)

async def handle_ide_message(user_text: str, sender_id: str) -> Any:
    context = get_user_context(sender_id)
    session = get_agent_session(sender_id)
    result = await Runner.run(ide_agent, user_text, context=context, session=session)
    
    # Because of output_type, result.final_output will now be an IDEResponse Pydantic object!
    return result.final_output