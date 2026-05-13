from dotenv import load_dotenv
import os
import requests
import json

load_dotenv()
def delete_default_event(function_slug: str, function_id: str):
    
    token = os.getenv("BEARER_TOKEN")
    org_id = os.getenv("ORG_ID")
    
    print("hello")
    headers = {
        "X-Organization-ID": org_id,
        "Authorization": f"Bearer {token}"
    }
    print(org_id)
    # STEP 1: Get events
    events_url = f"https://cortexone.rival.io/api/v1/functions/agent-foundry/{function_slug}/events"

    events_response = requests.request(
        "GET",
        events_url,
        headers=headers
    )

    events_data = events_response.json()
    print(json.dumps(events_data, indent=2))
    default_event_id = None

    # STEP 2: Find event where name == default
    for event in events_data.get("data", []):
        if event.get("event_name", "").lower() == "default":
            default_event_id = event["id"]
            print("Found even_name")
            break

    if not default_event_id:
        return {"error": "Default event not found"}

    # STEP 3: Delete event
    delete_url = f"https://cortexone.rival.io/api/v1/events/{default_event_id}/function/{function_id}"

    delete_response = requests.request(
        "DELETE",
        delete_url,
        headers=headers
    )

    return delete_response.json()


if __name__ == '__main__':
    print(
        delete_default_event(
            function_slug="base64-security-auditor",
            function_id="bf1fe3c0-4218-42ff-8886-c1cff06d6569"
        )
    )