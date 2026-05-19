from dotenv import load_dotenv
import os

load_dotenv()



def generate_and_save_long_description(
    function_slug: str,
    function_name: str,
    short_description: str
):
    
    token = os.getenv("BEARER_TOKEN")
    org_id = os.getenv("ORG_ID")
    import requests
    import json

    headers = {
        "X-Organization-ID": org_id,
        "Authorization": f"Bearer {token}"
    }

    # =====================================
    # STEP 1: CALL RIVAL ASSISTANT
    # =====================================

    rival_url = "https://cortexone.rival.io/api/app/rival-assistant"

    rival_payload = json.dumps({
        "prompt": "Generate an overview with strengths and limitations for this tool",
        "chats": [],
        "context": {},
        "event": 11,
        "meta": {
            "name": function_name,
            "description": short_description
        }
    })

    rival_response = requests.post(
        rival_url,
        headers={
            **headers,
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        },
        data=rival_payload,
        stream=True
    )

    final_overview = None

    # =====================================
    # STEP 2: PARSE EVENT STREAM
    # =====================================

    for line in rival_response.iter_lines():

        if line:

            decoded = line.decode("utf-8")

            print(decoded)

            if decoded.startswith("data:"):

                try:

                    data = json.loads(
                        decoded.replace("data: ", "")
                    )

                    # FINAL EVENT
                    if data.get("event") == "done":

                        final_overview = data["response"]["overview"]

                except Exception:
                    pass

    if not final_overview:
        return {
            "error": "Failed to generate overview"
        }

    # =====================================
    # STEP 3: CONVERT TO STRING
    # =====================================

    long_description = json.dumps({
        "what_it_does": final_overview["what_it_does"],
        "how_it_works": final_overview["how_it_works"],
        "strengths": final_overview["strengths"],
        "limitations": final_overview["limitations"],
        "long_description": final_overview.get(
            "long_description",
            ""
        )
    })

    # =====================================
    # STEP 4: SAVE TO DETAILS API
    # =====================================

    details_url = f"https://cortexone.rival.io/api/v1/function/agent-foundry/{function_slug}/details"

    details_payload = json.dumps({
        "orgSlug": "agent-foundry",
        "fnSlug": function_slug,
        "long_description": long_description
    })

    save_response = requests.request(
        "PUT",
        details_url,
        headers={
            **headers,
            "Content-Type": "application/json"
        },
        data=details_payload
    )

    return save_response.json()


if __name__ == "__main__":
    
    print(
        generate_and_save_long_description(
            function_slug="chord-transposition-assistant",
            function_name="Chord Transposition Assistant",
            short_description="Validates and transposes musical chords using a 12-tone chromatic scale with AI-based context verification and detailed theoretical insights."
        )
    )