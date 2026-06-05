from fastapi import FastAPI, Request, BackgroundTasks
import os
import requests
import json
import uuid
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# ==========================================
# 🔥 PATH INJECTION FOR GLOBAL IMPORTS
# ==========================================
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
LOCAL_DEPLOYMENT_DIR = ROOT_DIR / "Local_Rival_Deployment"
sys.path.insert(0, str(LOCAL_DEPLOYMENT_DIR))

# Import your core tools
from agent_core import handle_user_message
from session import get_user_context
from token_auth import token_manager  

load_dotenv()

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "mytoken")
ORG_ID = os.getenv("ORG_ID")

app = FastAPI()

RECENT_MESSAGE_IDS = []
MAX_CACHE_SIZE = 100

# ==========================================
# 🛡️ GUARDED HTTP REQUEST HELPER
# ==========================================
def make_guarded_cortex_request(method: str, url: str, **kwargs) -> requests.Response:
    """Wraps raw HTTP requests to automatically catch 401s and refresh the token."""
    token_manager.ensure_valid_token()
    
    # Inject the freshest token from the manager safely
    headers = kwargs.pop("headers", {})
    headers["Authorization"] = f"Bearer {token_manager.session_token}"
    kwargs["headers"] = headers
    
    # Make the first attempt
    res = requests.request(method, url, **kwargs)
    
    # If the token died exactly at this moment (HTTP 401 or 403)
    if res.status_code in (401, 403):
        print(f"⚠️ {res.status_code} Unauthorized for {url}. Refreshing token...")
        token_manager.refresh()
        headers["Authorization"] = f"Bearer {token_manager.session_token}"
        kwargs["headers"] = headers
        
        # Retry the request with the new token
        res = requests.request(method, url, **kwargs)
        
    return res


def send_whatsapp_message(to: str, text: str, buttons: list = None) -> None:
    """Sends a text message or an interactive button menu to a user."""
    if not ACCESS_TOKEN or not PHONE_NUMBER_ID:
        print("🚨 ERROR: ACCESS_TOKEN or PHONE_NUMBER_ID missing from .env!")
        return

    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    if buttons:
        formatted_buttons = [
            {"type": "reply", "reply": {"id": b["id"], "title": b["title"][:30]}} for b in buttons[:3]
        ]
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": text},
                "action": {"buttons": formatted_buttons}
            }
        }
    else:
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text},
        }

    requests.post(url, headers=headers, json=data, timeout=30)


def stream_agent_chat_to_string(agent_id: str, conversation_id: str, message: str) -> str:
    """Calls the streaming endpoint, blocks until complete, and returns the full text at once."""
    url = f"https://cortexone.rival.io/api/v1/rival-agents/{agent_id}/chat/stream"
    headers = {
        "X-Organization-ID": ORG_ID,
        "Content-Type": "application/json"
    }
    payload = {"conversation_id": conversation_id, "message": message}
    
    try:
        res = make_guarded_cortex_request("POST", url, headers=headers, json=payload, stream=True, timeout=120)
        
        if res.status_code != 200:
            return f"⚠️ Agent Error ({res.status_code}): Could not fetch message response."

        current_event = None
        accumulated_text = ""
        
        for line in res.iter_lines():
            if not line:
                continue
                
            decoded_line = line.decode('utf-8')
            
            if decoded_line.startswith("event:"):
                current_event = decoded_line.split("event:", 1)[1].strip()
                
            elif decoded_line.startswith("data:"):
                data_content = decoded_line.split("data:", 1)[1]
                if data_content.startswith(" "):
                    data_content = data_content[1:]
                
                if current_event == "token":
                    accumulated_text += data_content
                elif current_event == "done":
                    try:
                        final_json = json.loads(data_content.strip())
                        content = final_json.get("message", {}).get("content", "")
                        if content:
                            return content  
                    except json.JSONDecodeError:
                        pass 
                        
        if accumulated_text.strip():
            return accumulated_text.strip()
            
    except requests.exceptions.ReadTimeout:
        return "⚠️ The agent took too long to think and the connection timed out."
    except Exception as e:
        return f"🚨 Connection Error while streaming agent: {e}"
        
    return "⚠️ Agent completed the task but returned an empty response."


def process_background_pipeline(sender: str, text: str = None, interactive_reply: dict = None):
    """Processes pipeline events out-of-band to maintain immediate 200 OK responses."""
    ctx = get_user_context(sender)

    # ==========================================
    # FLOW A: User Clicked an Interactive Button
    # ==========================================
    if interactive_reply:
        button_id = interactive_reply.get("id", "")
        button_title = interactive_reply.get("title", "")

        if button_id == "exit_agent_session":
            send_whatsapp_message(sender, f"🚪 Exited session with {ctx.active_agent_name}. Returning to Main Developer Assistant.")
            ctx.active_agent_id = None
            ctx.active_agent_name = None
            ctx.agent_conversation_id = None
            return

        if button_id.startswith("adopt_"):
            listing_id = button_id.replace("adopt_", "")
            send_whatsapp_message(sender, f"🤝 Establishing link with '{button_title}'... Please hold.")
            
            adopt_url = f"https://cortexone.rival.io/api/v1/rival-agent-listings/{listing_id}/adopt"
            headers = {"X-Organization-ID": ORG_ID}
            
            try:
                adopt_res = make_guarded_cortex_request("POST", adopt_url, headers=headers, timeout=30)
                
                if adopt_res.status_code in (200, 201):
                    data = adopt_res.json().get("data", {})
                    ctx.active_agent_id = data.get("agent_id")
                    ctx.active_agent_name = button_title
                    ctx.agent_conversation_id = str(uuid.uuid4())
                    
                    send_whatsapp_message(
                        sender, 
                        f"🚀 Connection Open! You are now speaking with *{button_title}*. All future messages go directly to them.",
                        buttons=[{"id": "exit_agent_session", "title": "Exit Agent"}]
                    )
                else:
                    send_whatsapp_message(sender, "❌ Failed to adopt agent. Returning to standard chat.")
            except Exception as e:
                send_whatsapp_message(sender, f"🚨 System deployment error: {e}")
            return

    # ==========================================
    # FLOW B: Standard Text Messaging / Proxy Routing
    # ==========================================
    if text:
        if text.strip().lower() in ["exit", "exit agent", "quit"]:
            if ctx.active_agent_id:
                send_whatsapp_message(sender, f"🚪 Closed session with {ctx.active_agent_name}. Welcome back!")
                ctx.active_agent_id = None
                ctx.active_agent_name = None
                ctx.agent_conversation_id = None
                return

        if ctx.active_agent_id:
            response_text = stream_agent_chat_to_string(ctx.active_agent_id, ctx.agent_conversation_id, text)
            send_whatsapp_message(
                sender, 
                response_text, 
                buttons=[{"id": "exit_agent_session", "title": "Exit Agent"}]
            )
            return

        if "search agent" in text.lower() or "find agent" in text.lower():
            ctx.pending_search_query = True
            send_whatsapp_message(sender, "🔍 What kind of agents do you want to look for? Enter search keywords:")
            return

        if ctx.pending_search_query:
            ctx.pending_search_query = False
            search_url = "https://cortexone.rival.io/api/v2/search/quick?limit=3"
            headers = {"X-Organization-ID": ORG_ID, "Content-Type": "application/json"}
            payload = {
                "query": text,
                "search_in": {"functions": False, "digital_assets": False, "is_author": False, "is_organization": False, "is_agent": True}
            }
          
            try:
                res = make_guarded_cortex_request("POST", search_url, headers=headers, json=payload, timeout=20)
                
                agents = res.json().get("data", {}).get("items", {}).get("agents", [])
                if not agents:
                    send_whatsapp_message(sender, f"⚠️ No matches found for '{text}'.")
                    return

                buttons = [{"id": f"adopt_{a['listing_id']}", "title": a['name']} for a in agents[:3]]
                send_whatsapp_message(sender, f"💡 Top agents matching '{text}': Select one below to begin chatting:", buttons=buttons)
            except Exception as e:
                send_whatsapp_message(sender, f"🚨 Elastic Search failed: {e}")
            return

        # Explicitly initialize the asyncio loop cleanly to avoid memory leaks
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            response_text = loop.run_until_complete(handle_user_message(text, sender))
        finally:
            loop.close()
            
        send_whatsapp_message(sender, response_text)


@app.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params
    if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == VERIFY_TOKEN:
        return int(params.get("hub.challenge", 0))
    return "Verification failed"


@app.post("/webhook")
async def webhook_handler(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    try:
        value = data["entry"][0]["changes"][0]["value"]
        if "messages" not in value:
            return {"status": "ok"}
            
        message_data = value["messages"][0]
        sender = message_data["from"]
        message_id = message_data.get("id")

        if message_id in RECENT_MESSAGE_IDS:
            return {"status": "ok"}
        RECENT_MESSAGE_IDS.append(message_id)
        if len(RECENT_MESSAGE_IDS) > MAX_CACHE_SIZE:
            RECENT_MESSAGE_IDS.pop(0)

        if message_data.get("type") == "text":
            text_body = message_data["text"]["body"]
            background_tasks.add_task(process_background_pipeline, sender, text=text_body)
        
        elif message_data.get("type") == "interactive":
            reply_data = message_data["interactive"]["button_reply"]
            background_tasks.add_task(process_background_pipeline, sender, interactive_reply=reply_data)

    except Exception as e:
        print(f"🚨 Webhook handler encountered an anomaly: {e}")

    return {"status": "ok"}