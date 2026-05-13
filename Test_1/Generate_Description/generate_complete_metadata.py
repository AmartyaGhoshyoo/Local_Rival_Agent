from dotenv import load_dotenv
import os

load_dotenv()




def auto_generate_complete_metadata(function_slug: str):
    token = os.getenv("BEARER_TOKEN")
    org_id = os.getenv("ORG_ID")

    import requests
    import json

    headers = {
        "X-Organization-ID": org_id,
        "Authorization": f"Bearer {token}"
    }

    # =========================================================
    # STEP 1: GET FUNCTION DETAILS
    # =========================================================

    details_url = f"https://cortexone.rival.io/api/v1/function/agent-foundry/{function_slug}/details"

    details_response = requests.request(
        "GET",
        details_url,
        headers=headers
    )

    details_data = details_response.json()["data"]

    function_id = details_data["function_id"]

    function_name = details_data["function_name"]

    short_description = details_data["short_description"]

    runtime = details_data["versions"][0]["runtime"]

    files = details_data["versions"][0]["files"]

    # =========================================================
    # STEP 2: BUILD CODE PAYLOAD
    # =========================================================

    code_payload = []

    for file in files:

        code_payload.append({
            "filename": file["meta"]["name"],
            "data": file["data"],
            "path": file["path"]
        })

    # =========================================================
    # STEP 3: GENERATE OVERVIEW
    # =========================================================

    overview_payload = {
        "prompt": "Generate an overview with strengths and limitations for this tool",
        "chats": [],
        "context": {},
        "event": 11,
        "meta": {
            "name": function_name,
            "description": short_description
        }
    }

    rival_url = "https://cortexone.rival.io/api/app/rival-assistant"

    overview_response = requests.post(
        rival_url,
        headers={
            **headers,
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        },
        data=json.dumps(overview_payload),
        stream=True
    )

    final_overview = None

    for line in overview_response.iter_lines():

        if line:

            decoded = line.decode("utf-8")

            print(decoded)

            if decoded.startswith("data:"):

                try:

                    parsed = json.loads(
                        decoded.replace("data: ", "")
                    )

                    if parsed.get("event") == "done":

                        final_overview = parsed["response"]["overview"]

                except Exception:
                    pass

    if not final_overview:

        return {
            "error": "Overview generation failed"
        }

    # =========================================================
    # STEP 4: GENERATE DOCUMENTATION
    # =========================================================

    documentation_payload = {
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

    documentation_response = requests.post(
        rival_url,
        headers={
            **headers,
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        },
        data=json.dumps(documentation_payload),
        stream=True
    )

    final_documentation = None

    for line in documentation_response.iter_lines():

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

    # =========================================================
    # STEP 5: COMBINE OVERVIEW + DOCUMENTATION
    # =========================================================

    combined_long_description = json.dumps({

        "what_it_does":
        final_overview.get("what_it_does", ""),

        "how_it_works":
        final_overview.get("how_it_works", ""),

        "overview":
        final_overview.get("what_it_does", ""),

        "strengths":
        final_overview.get("strengths", []),

        "limitations":
        final_overview.get("limitations", []),

        "long_description":
        final_documentation

    })

    # =========================================================
    # STEP 6: SAVE DETAILS
    # =========================================================

    save_payload = {
        "orgSlug": "agent-foundry",
        "fnSlug": function_slug,
        "long_description": combined_long_description
    }

    save_response = requests.request(
        "PUT",
        details_url,
        headers={
            **headers,
            "Content-Type": "application/json"
        },
        data=json.dumps(save_payload)
    )

    print(save_response.json())

    # =========================================================
    # STEP 7: GENERATE CHANGELOG
    # =========================================================

    changelog_payload = {
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

    changelog_response = requests.post(
        rival_url,
        headers={
            **headers,
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        },
        data=json.dumps(changelog_payload),
        stream=True
    )

    final_changelog = None

    for line in changelog_response.iter_lines():

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
            "error": "Changelog generation failed"
        }

    # =========================================================
    # STEP 8: SAVE CHANGELOG
    # =========================================================

    changelog_url = f"https://cortexone.rival.io/api/v1/functions/{function_id}/changelog"

    changelog_save_payload = {
        "version": "draft",
        "changelog": final_changelog
    }

    changelog_save_response = requests.request(
        "PUT",
        changelog_url,
        headers={
            **headers,
            "Content-Type": "application/json"
        },
        data=json.dumps(changelog_save_payload)
    )

    return {
        "details_response": save_response.json(),
        "changelog_response": changelog_save_response.json(),
        "generated_overview": final_overview,
        "generated_documentation": final_documentation,
        "generated_changelog": final_changelog
    }


if __name__ == "__main__":

    print(
        auto_generate_complete_metadata(
            "chord-transposition-assistant"
        )
    )