from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os

# 🔥 Load the .env file into memory first
from dotenv import load_dotenv
load_dotenv()

# Now it is safe to import your agent, because os.environ has the tokens
from AI_Agent_RIval import run_agent

app = FastAPI()

# Allow frontend to talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

class CodeRequest(BaseModel):
    filename: str
    code: str

@app.post("/api/execute")
def execute_code(request: CodeRequest):
    run_context: dict = {}
    try:
        # Run your agent directly (FastAPI handles the threading natively)
        run_result = run_agent(request.code, run_context)

        # Matches the UI's expectation of result.message
        return {
            "status": "success",
            "filename": request.filename,
            "message": "Execution completed successfully.",
            "function_name": run_result.get("function_name"),
            "function_slug": run_result.get("function_slug"),
            "function_id": run_result.get("function_id"),
            "result": run_result,
        }

    except Exception as e:
        # Matches the UI's expectation of result.detail.error; include any
        # platform identifiers collected before the failure (e.g. changelog hang).
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "filename": request.filename,
                "function_name": run_context.get("function_name"),
                "function_slug": run_context.get("function_slug"),
                "function_id": run_context.get("function_id"),
            },
        )