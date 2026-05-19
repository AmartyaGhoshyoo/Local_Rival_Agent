from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def run_cortexone_handler(code: str, event: dict, timeout_sec: int = 45) -> str:
    """
    Write `code` to a temp module and invoke cortexone_handler(event, None) in a subprocess.
    Returns a human-readable report (stdout + stderr + exit code).
    """
    root = _project_root()
    wa_dir = root / "WhatsAPP_Agent"
    wa_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix="_wa_user_function.py",
        delete=False,
        encoding="utf-8",
        dir=str(wa_dir),
    ) as code_f:
        code_f.write(code)
        code_path = code_f.name

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix="_wa_event.json",
        delete=False,
        encoding="utf-8",
        dir=str(wa_dir),
    ) as ev_f:
        json.dump(event, ev_f)
        event_path = ev_f.name

    try:
        runner = textwrap.dedent(
            f"""
            import importlib.util
            import json
            import sys

            code_path = {json.dumps(code_path)}
            event_path = {json.dumps(event_path)}

            with open(event_path, "r", encoding="utf-8") as f:
                event = json.load(f)

            spec = importlib.util.spec_from_file_location("user_fn", code_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if not hasattr(mod, "cortexone_handler"):
                print("ERROR: cortexone_handler not defined", file=sys.stderr)
                sys.exit(2)
            out = mod.cortexone_handler(event, None)
            print(json.dumps(out, indent=2, default=str))
            """
        ).strip()

        proc = subprocess.run(
            [sys.executable, "-c", runner],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            env={**os.environ, "PYTHONUTF8": "1"},
        )
        parts = []
        if proc.stdout:
            parts.append("--- stdout ---\n" + proc.stdout.strip())
        if proc.stderr:
            parts.append("--- stderr ---\n" + proc.stderr.strip())
        parts.append(f"--- exit_code ---\n{proc.returncode}")
        return "\n\n".join(parts)
    finally:
        for p in (code_path, event_path):
            try:
                os.unlink(p)
            except OSError:
                pass
