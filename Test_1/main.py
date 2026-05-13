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
    try:
        # Run your agent directly (FastAPI handles the threading natively)
        run_result = run_agent(request.code)
        
        # Matches the UI's expectation of result.message
        return {
            "status": "success", 
            "filename": request.filename,
            "message": "Execution completed successfully.",
            "result": run_result
        }
        
    except Exception as e:
        print(f"🚨 Crash in {request.filename}: {e}")
        # Matches the UI's expectation of result.detail.error
        raise HTTPException(status_code=500, detail={"error": str(e)})