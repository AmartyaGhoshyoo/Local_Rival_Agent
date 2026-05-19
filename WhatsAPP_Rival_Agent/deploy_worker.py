"""
Subprocess entry: deploy generated handler code via Local_Rival_Deployment run_agent.
Usage: python deploy_worker.py <path_to_code.txt>
Stdout: JSON string of run_agent return (best-effort).
Cwd is forced to Local_Rival_Deployment so relative imports (.env, token_auth) match production agent.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

def main() -> int:
    if len(sys.argv) < 2:
        print(json.dumps({"error": "usage: deploy_worker.py <code_file.txt>"}))
        return 1
    
    code_path = Path(sys.argv[1])
    code = code_path.read_text(encoding="utf-8")

    # 1. Resolve the path to the new directory
    root = Path(__file__).resolve().parent.parent
    local_rival_dir = root / "Local_Rival_Deployment"
    
    # 2. Change working directory and inject into system path
    os.chdir(local_rival_dir)
    sys.path.insert(0, str(local_rival_dir))

    # 3. Load the environment variables from the new directory
    from dotenv import load_dotenv
    load_dotenv(local_rival_dir / ".env")

    # 4. Safely import and run the agent
    from AI_Agent_RIval import run_agent

    ctx: dict = {}
    result = run_agent(code, ctx)
    print(json.dumps({"ok": True, "result": result, "run_context": ctx}, default=str))
    
    return 0

if __name__ == "__main__":
    raise SystemExit(main())