from fastapi import FastAPI, Request, BackgroundTasks
import os
import requests
from dotenv import load_dotenv
import json

from agent_core import handle_user_message

load_dotenv()

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "mytoken")

app = FastAPI()

# 🔥 DEDUPLICATION CACHE
# Stores the unique IDs of recently processed messages so we don't process them twice.
RECENT_MESSAGE_IDS = []
MAX_CACHE_SIZE = 100

def send_whatsapp_message(to: str, text: str) -> None:
    if not ACCESS_TOKEN or not PHONE_NUMBER_ID:
        print("🚨 ERROR: ACCESS_TOKEN or PHONE_NUMBER_ID is missing from .env!")
        return

    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    max_body = 4000
    chunks = []
    if len(text) <= max_body:
        chunks.append(text)
    else:
        for i in range(0, len(text), max_body):
            part = text[i : i + max_body]
            n = i // max_body + 1
            chunks.append(f"(part {n}/{-(-len(text) // max_body)})\n{part}")

    for body in chunks:
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": body},
        }
        print(f"📤 Sending WhatsApp reply to {to}...")
        response = requests.post(url, headers=headers, json=data, timeout=60)
        
        if response.status_code != 200:
            print(f"❌ Failed to send message: {response.text}")
        else:
            print(f"✅ Message sent successfully!")

async def process_ai_response_in_background(message_text: str, sender: str):
    """This runs in the background so Meta doesn't time out."""
    try:
        response_text = await handle_user_message(message_text, sender)
        send_whatsapp_message(sender, response_text)
    except Exception as e:
        print(f"🚨 SERVER CRASH IN AI TASK: {e}")


@app.get("/webhook")
async def verify(request: Request):
    hub_mode = request.query_params.get("hub.mode")
    hub_verify_token = request.query_params.get("hub.verify_token")
    hub_challenge = request.query_params.get("hub.challenge")

    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return int(hub_challenge)

    return {"error": "Verification failed"}


@app.post("/webhook")
async def webhook(request: Request, background_tasks: BackgroundTasks): 
    data = await request.json()

    try:
        value = data["entry"][0]["changes"][0]["value"]
        
        if "messages" not in value:
            return {"status": "ok"}
            
        message_data = value["messages"][0]
        sender = message_data["from"]
        
        # 🔥 Extract the unique WhatsApp Message ID
        message_id = message_data.get("id")

        if message_data.get("type") == "text":
            # 🔥 Check if we've already seen this exact message
            if message_id in RECENT_MESSAGE_IDS:
                print(f"♻️ Ignored Meta Retry (Duplicate Message ID: {message_id})")
                return {"status": "ok"}
            
            # 🔥 If it's new, add it to our list
            RECENT_MESSAGE_IDS.append(message_id)
            if len(RECENT_MESSAGE_IDS) > MAX_CACHE_SIZE:
                RECENT_MESSAGE_IDS.pop(0) # Keep the cache small so we don't run out of RAM

            message_text = message_data["text"]["body"]
            print(f"\n📩 Received message from {sender}: {message_text}")
            print("🧠 AI is thinking...")
            
            background_tasks.add_task(process_ai_response_in_background, message_text, sender)
            
        else:
            print(f"⚠️ Ignored non-text message type: {message_data.get('type')}")

    except Exception as e:
        print(f"\n🚨 SERVER CRASH IN WEBHOOK ROUTING: {e}")

    # INSTANTLY returns 200 OK so Meta never retries!
    return {"status": "ok"}