import os
import asyncio
from fastapi import FastAPI, Request, BackgroundTasks
from dotenv import load_dotenv
from agent_core_resume import handle_user_message
from whatsapp_api import send_text_message

load_dotenv()
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")

app = FastAPI()
PROCESSED_MESSAGES = set()

def process_agent_workflow(sender_id: str, text: str):
    """Runs the agent runner in a new event loop for the background task."""
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        # 1. Run the agent brain
        response_text = loop.run_until_complete(handle_user_message(text, sender_id))
        # 2. Send the AI's conversational response back via WhatsApp
        if response_text:
            send_text_message(sender_id, response_text)
    finally:
        loop.close()

@app.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params
    if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == VERIFY_TOKEN:
        return int(params.get("hub.challenge", 0))
    return "Verification failed"

@app.post("/webhook")
async def receive_message(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    
    try:
        value = data["entry"][0]["changes"][0]["value"]
        if "messages" not in value:
            return {"status": "ok"}
            
        message = value["messages"][0]
        sender_id = message["from"]
        msg_id = message["id"]

        if msg_id in PROCESSED_MESSAGES:
            return {"status": "ok"}
        PROCESSED_MESSAGES.add(msg_id)

        if message.get("type") == "text":
            text = message["text"]["body"]
            # Fire the agent into the background
            background_tasks.add_task(process_agent_workflow, sender_id, text)

    except Exception as e:
        print("Webhook Error:", e)

    return {"status": "ok"}