import os
import json
import uuid
import requests
from dotenv import load_dotenv

load_dotenv()

def test_agent_workflow(search_query: str = "agents"):
    token = os.getenv("BEARER_TOKEN")
    org_id = os.getenv("ORG_ID")

    if not token or not org_id:
        raise ValueError("🚨 Missing BEARER_TOKEN or ORG_ID in environment variables.")

    headers = {
        "X-Organization-ID": org_id,
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # ==========================================
    # STEP 1: SEARCH FOR AGENTS
    # ==========================================
    print(f"\n🔍 STEP 1: Searching for '{search_query}'...")
    search_url = "https://cortexone.rival.io/api/v2/search/quick?limit=5"
    search_payload = {
        "query": search_query,
        "search_in": {
            "functions": False,
            "digital_assets": False,
            "is_author": False,
            "is_organization": False,
            "is_agent": True
        }
    }

    search_res = requests.post(search_url, headers=headers, json=search_payload)
    
    if search_res.status_code != 200:
        raise Exception(f"🚨 Search API Failed: {search_res.text}")

    search_data = search_res.json().get("data", {}).get("items", {}).get("agents", [])
    
    if not search_data:
        raise Exception("⚠️ No agents found in the search results.")

    # Grab the first agent in the list for testing
    first_agent = search_data[0]
    listing_id = first_agent["listing_id"]  # ID from elastic search
    agent_name = first_agent["name"]
    
    print(f"✅ Found Agent: {agent_name} (Listing ID: {listing_id})")

    # ==========================================
    # STEP 2: ADOPT THE AGENT
    # ==========================================
    print(f"\n🤝 STEP 2: Adopting Agent '{agent_name}'...")
    adopt_url = f"https://cortexone.rival.io/api/v1/rival-agent-listings/{listing_id}/adopt"
    
    adopt_res = requests.post(adopt_url, headers=headers)
    
    if adopt_res.status_code != 201:
        raise Exception(f"🚨 Adopt API Failed: {adopt_res.text}")
        
    adopt_data = adopt_res.json().get("data", {})
    adopted_agent_id = adopt_data.get("agent_id")
    
    print(f"✅ Successfully Adopted! New Agent ID: {adopted_agent_id}")

    # ==========================================
    # STEP 3: CHAT WITH THE AGENT (STREAMING)
    # ==========================================
    print(f"\n💬 STEP 3: Initiating Chat Stream with Agent ID: {adopted_agent_id}...")
    chat_url = f"https://cortexone.rival.io/api/v1/rival-agents/{adopted_agent_id}/chat/stream"
    
    # Generate a random conversation ID for this test session
    conversation_id = str(uuid.uuid4())
    test_message = "Hi, what can you do to help me?"
    
    chat_payload = {
        "conversation_id": conversation_id,
        "message": test_message
    }

    print(f"👤 You: {test_message}")
    print(f"🤖 {agent_name}: ", end="", flush=True)

    # Note: stream=True is critical for SSE
    chat_res = requests.post(chat_url, headers=headers, json=chat_payload, stream=True)
    
    if chat_res.status_code != 200:
        raise Exception(f"\n🚨 Chat API Failed: {chat_res.text}")

    # --- Lightweight SSE Parser ---
    current_event = None
    
    for line in chat_res.iter_lines():
        if not line:
            continue
            
        decoded_line = line.decode('utf-8').strip()
        
        # Capture the event type
        if decoded_line.startswith("event:"):
            current_event = decoded_line.split("event:", 1)[1].strip()
            
        # Capture the data payload
        elif decoded_line.startswith("data:"):
            data_content = decoded_line.split("data:", 1)[1].strip()
            
            # Print tokens as they arrive for a typewriter effect
            if current_event == "token":
                print(data_content, end="", flush=True)
                
            # If done, we can optionally parse the final JSON block
            elif current_event == "done":
                # final_data = json.loads(data_content)
                break

    print("\n\n🏁 Test complete!")

if __name__ == '__main__':
    try:
        test_agent_workflow()
    except Exception as e:
        print(f"\n❌ Error during execution: {e}")