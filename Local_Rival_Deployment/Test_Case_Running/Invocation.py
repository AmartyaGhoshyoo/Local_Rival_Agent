from dotenv import load_dotenv
import os

load_dotenv()


def invoke_all_non_default_events(function_slug: str, function_id: str):
    token = os.getenv("BEARER_TOKEN")
    org_id = os.getenv("ORG_ID")
    import requests
    import json

    headers = {
        "X-Organization-ID": org_id,
        "Authorization": f"Bearer {token}"
    }

    # STEP 1: GET DETAILS → extract files
    details_url = f"https://cortexone.rival.io/api/v1/function/agent-foundry/{function_slug}/details"

    details_response = requests.request(
        "GET",
        details_url,
        headers=headers
    )
    
    if details_response.status_code != 200:
        raise Exception(f"Details API Failed: {details_response.text}")

    details_data = details_response.json()["data"]

    function_id = details_data["function_id"]
    
    # We extract these to build the payload, but we MUST use function_slug in the URL
    function_name = details_data["function_name"]
    short_description = details_data["short_description"]
    runtime = details_data["versions"][0]["runtime"]
    handler = details_data["versions"][0]["handler"]
    files = details_data["versions"][0]["files"]

# STEP 2: GET EVENTS
    events_url = f"https://cortexone.rival.io/api/v1/functions/agent-foundry/{function_slug}/events"
    events_response = requests.request("GET", events_url, headers=headers)
    
    if events_response.status_code != 200:
        raise Exception(f"🚨 Events API Failed: {events_response.text}")
        
    events_res = events_response.json()
    
    # 🔥 DEBUG 1: Print exactly how many events the platform found
    events_list = events_res.get("data", [])
    print(f"\n🔍 DEBUG: Found {len(events_list)} total events for this function.")

    results = []
    for event in events_list:
        event_name = event.get('event_name', 'Unknown Test')
        
        if event.get("is_default") is not True:
            invocation_url = f"https://cortexconnect.rival.io/api/v1/functions/{function_slug}/invocations"

            payload = json.dumps({
                "user_id": "U3AnRAXmf9R4rNfKdqQcTd5l7qOF",
                "function_id": function_id,
                "function_name": function_name, 
                "version": "draft",
                "runtime": runtime,
                "handler": handler,
                "timeout": 300,
                "environment_variable": [
"9140ed62-61b4-4b33-850c-7f458a7a612a"],
                "event": event.get("event_data", {}),
                "files": files
            })

            response = requests.request(
                "POST",
                invocation_url,
                headers={**headers, "Content-Type": "application/json"},
                data=payload
            )

            res_json = response.json()
            print(res_json)
            
            # 🔥 Clean up the result for the UI
            results.append({
                "test_name": event_name,
                "result": res_json.get("result", "No result returned")
            })

    return results


if __name__ == '__main__':
    import json
    data = invoke_all_non_default_events(
        function_slug="entropy-split-intelligence-evaluator",
        function_id="e2b4b044-7dbf-466c-9863-45c0039856ce"
    )
    print(json.dumps(data, indent=2))