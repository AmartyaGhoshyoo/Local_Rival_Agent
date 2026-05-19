from dotenv import load_dotenv
import os
import requests
import json

load_dotenv()

def release_function(
    function_slug: str,
    function_id: str,
    generated_changelog: str
):
    token = os.getenv("BEARER_TOKEN")
    org_id = os.getenv("ORG_ID")

    headers = {
        "X-Organization-ID": org_id,
        "Authorization": f"Bearer {token}"
    }


    # STEP 1: GET EVENTS → collect all event_ids
    events_url = f"https://cortexone.rival.io/api/v1/functions/agent-foundry/{function_slug}/events"
    events_res = requests.get(events_url, headers=headers).json()
    event_ids = [event["id"] for event in events_res.get("data", [])]

    # STEP 2: GET DETAILS → extract files + runtime
    details_url = f"https://cortexone.rival.io/api/v1/function/agent-foundry/{function_slug}/details"
    details_res = requests.get(details_url, headers=headers).json()
    
    version = details_res["data"]["versions"][0]
    files = version["files"]
    runtime = version["runtime"]

    # STEP 3: RELEASE
    release_url = f"https://cortexone.rival.io/api/v1/functions/{function_id}/release"

    payload = {
        "changelog": generated_changelog,
        "compute_type": "CPU",
        "event_ids": event_ids,
        "files": files,
        "price_per_api_request": 0,
        "runtime": runtime,
        "version": "1.0.0",
        "visibility": "private"
    }

    response = requests.put(
        release_url,
        headers={**headers, "Content-Type": "application/json"},
        json=payload
    )

    return response.json()

if __name__ == "__main__":
    function_slug = "cortexone-acoustic-analysis-handler"
    function_id = "16cb5efc-fce3-4f10-8b0b-aeb86843c28e"

    try:
        response = release_function(function_slug, function_id)
        print("\n🎉 Final Response:")
        print(json.dumps(response, indent=2))
    except Exception as e:
        print("\n❌ Error:", str(e))