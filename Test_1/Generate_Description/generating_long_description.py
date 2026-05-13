from dotenv import load_dotenv
import os

load_dotenv()

token = os.getenv("BEARER_TOKEN")
org_id = os.getenv("ORG_ID")

def generate_and_save_documentation(function_slug: str):

    import requests
    import json

    headers = {
        "X-Organization-ID": org_id,
        "Authorization": f"Bearer {token}"
    }

    # ==========================================
    # STEP 1: GET FUNCTION DETAILS
    # ==========================================

    details_url = f"https://cortexone.rival.io/api/v1/function/agent-foundry/{function_slug}/details"

    details_response = requests.request(
        "GET",
        details_url,
        headers=headers
    )

    details_data = details_response.json()["data"]

    # ==========================================
    # STEP 2: EXTRACT DATA
    # ==========================================

    function_name = details_data["function_name"]

    short_description = details_data["short_description"]

    runtime = details_data["versions"][0]["runtime"]

    files = details_data["versions"][0]["files"]

    # Convert files format for rival assistant
    code_payload = []

    for file in files:

        code_payload.append({
            "filename": file["meta"]["name"],
            "data": file["data"],
            "path": file["path"]
        })

    # ==========================================
    # STEP 3: BUILD RIVAL ASSISTANT PAYLOAD
    # ==========================================

    rival_payload = {
        "prompt": "Generate documentation for this tool",
        "chats": [],
        "context": {},
        "event": 10,
        "meta": {
            "name": function_name,
            "description": short_description,
            "runtime": runtime
        },
        "code": code_payload
    }

    # ==========================================
    # STEP 4: CALL RIVAL ASSISTANT
    # ==========================================

    rival_url = "https://cortexone.rival.io/api/app/rival-assistant"

    response = requests.post(
        rival_url,
        headers={
            **headers,
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        },
        data=json.dumps(rival_payload),
        stream=True
    )

    final_documentation = None

    # ==========================================
    # STEP 5: READ EVENT STREAM
    # ==========================================

    for line in response.iter_lines():

        if line:

            decoded = line.decode("utf-8")

            print(decoded)

            if decoded.startswith("data:"):

                try:

                    parsed = json.loads(
                        decoded.replace("data: ", "")
                    )

                    if parsed.get("event") == "done":

                        final_documentation = parsed["response"]["documentation"]

                except Exception:
                    pass

    if not final_documentation:
        return {
            "error": "Documentation generation failed"
        }

    # ==========================================
    # STEP 6: BUILD LONG DESCRIPTION
    # ==========================================

    long_description_payload = json.dumps({
        "long_description": final_documentation
    })

    # ==========================================
    # STEP 7: SAVE TO DETAILS API
    # ==========================================

    save_payload = json.dumps({
        "orgSlug": "agent-foundry",
        "fnSlug": function_slug,
        "long_description": long_description_payload
    })

    save_response = requests.request(
        "PUT",
        details_url,
        headers={
            **headers,
            "Content-Type": "application/json"
        },
        data=save_payload
    )

    return save_response.json()


if __name__ == "__main__":

    print(
        generate_and_save_documentation(
            "chord-transposition-assistant"
        )
    )