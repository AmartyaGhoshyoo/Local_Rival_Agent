from fastapi import FastAPI
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import time
from ide_agent_core import handle_ide_message

load_dotenv()

app = FastAPI(title="Rival IDE Extension Backend")

class IDEChatRequest(BaseModel):
    user_message: str
    source_code: str
    file_name: str
    file_path: str
    user_id: str = "ide_user_local_22"

@app.post("/ide-chat")
async def handle_ide_chat(request: IDEChatRequest):
    try:
        print(f"\n💻 [VS Code] Received: {request.user_message}")
        print(f"📂 [VS Code] Target File: {request.file_name}")
        
        full_prompt = (
            f"User Command: {request.user_message}\n\n"
            f"Active File Name: {request.file_name}\n"
            f"Absolute File Path: {request.file_path}\n"
            f"Current Code in Editor:\n```python\n{request.source_code}\n```"
        )
        print("Time at before agent",time.time())
        # This returns your beautifully structured Pydantic object
        agent_response = await handle_ide_message(full_prompt, request.user_id)
        
# Safely extract the data
        if hasattr(agent_response, 'reply'):
            reply_text = agent_response.reply
            new_code = agent_response.new_code
            ui_state = agent_response.ui_state
            raw_data = agent_response.raw_api_data
        elif isinstance(agent_response, dict):
            reply_text = agent_response.get("reply", "Done.")
            new_code = agent_response.get("new_code")
            ui_state = agent_response.get("ui_state", "normal")
            raw_data = agent_response.get("raw_api_data")
        else:
            reply_text = str(agent_response)
            new_code = None
            ui_state = "normal"
            raw_data = None

        print("✅ [VS Code] Structured payload dispatched.")
        return {
            "status": "success", 
            "reply": reply_text, 
            "new_code": new_code,
            "ui_state": ui_state,
            "raw_api_data": raw_data
        }
    except Exception as e:
        print(f"🚨 [VS Code] SERVER ERROR: {e}")
        return {"status": "error", "reply": f"Internal Server Error: {str(e)}", "new_code": None}