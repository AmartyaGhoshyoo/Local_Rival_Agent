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
    details_res = requests.request("GET", details_url, headers=headers).json()

    version_data = details_res["data"]["versions"][0]

    files = version_data["files"]
    runtime = version_data["runtime"]
    handler = version_data["handler"]

    # STEP 2: GET EVENTS
    events_url = f"https://cortexone.rival.io/api/v1/functions/agent-foundry/{function_slug}/events"
    events_res = requests.request("GET", events_url, headers=headers).json()

    results = []

    for event in events_res["data"]:

        if event.get("is_default") is False:

            invocation_url = f"https://cortexconnect.rival.io/api/v1/functions/{function_slug}/invocations"

            payload = json.dumps({
                "user_id": "U3AnRAXmf9R4rNfKdqQcTd5l7qOF",
                "function_id": function_id,
                "function_name": function_slug,
                "version": "Draft",
                "runtime": runtime,
                "handler": handler,
                "timeout": 300,
                "environment_variable": [],
                "event": event["event_data"],
                "files": files
            })

            response = requests.request(
                "POST",
                invocation_url,
                headers={**headers, "Content-Type": "application/json"},
                data=payload
            )

            results.append(response.json()) # ❗️❗️❗️❗️ AI WILL CHECK FIRST

    return results


if __name__ == '__main__':
    import json
    data=invoke_all_non_default_events(
        function_slug="awsdsadsadda",
        function_id="53d8fb3a-60e5-4849-8aaa-b30625ada974"
    )
    print(json.dumps(data,indent=2))