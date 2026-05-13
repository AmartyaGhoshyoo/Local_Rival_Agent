from dotenv import load_dotenv
import os

load_dotenv()

token = os.getenv("BEARER_TOKEN")
org_id = os.getenv("ORG_ID")

def generate_and_save_changelog(function_slug: str, function_id: str):

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

    files = details_data["versions"][0]["files"]

    # ==========================================
    # STEP 2: BUILD CODE PAYLOAD
    # ==========================================

    code_payload = []

    for file in files:

        code_payload.append({
            "data": file["data"],
            "path": file["path"],
            "meta": file["meta"]
        })

    # ==========================================
    # STEP 3: BUILD RIVAL ASSISTANT PAYLOAD
    # ==========================================

    rival_payload = {
        "prompt": "Generate a changelog for this release",
        "chats": [],
        "context": {},
        "event": 9,
        "code": code_payload,
        "versions": [
            {
                "version": "draft",
                "files": code_payload
            }
        ]
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

    final_changelog = None

    # ==========================================
    # STEP 5: READ SSE STREAM
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

                        final_changelog = parsed["response"]["reply"]

                except Exception:
                    pass

    if not final_changelog:

        return {
            "error": "Failed to generate changelog"
        }

    # ==========================================
    # STEP 6: SAVE CHANGELOG
    # ==========================================

    save_url = f"https://cortexone.rival.io/api/v1/functions/{function_id}/changelog"

    save_payload = {
        "version": "draft",
        "changelog": final_changelog
    }

    save_response = requests.request(
        "PUT",
        save_url,
        headers={
            **headers,
            "Content-Type": "application/json"
        },
        data=json.dumps(save_payload)
    )

    return save_response.json()


if __name__ == "__main__":

    print(
        generate_and_save_changelog(
            function_slug="chord-transposition-assistant",
            function_id="e067f8a1-2626-42bd-a124-520e96c61580"
        )
    )