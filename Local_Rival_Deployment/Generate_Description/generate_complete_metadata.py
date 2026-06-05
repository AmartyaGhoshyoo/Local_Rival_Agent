from dotenv import load_dotenv
import os
import requests
import json

load_dotenv()

def auto_generate_complete_metadata(function_slug: str):
    token = os.getenv("BEARER_TOKEN")
    org_id = os.getenv("ORG_ID")

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
    
    # Updated Endpoint URL
    rival_bot_url = "https://cortexone.rival.io/api/v1/rival-bot/conversations"

    overview_payload = {
        "event": 11,
        "function_id": function_id,
        "prompt": "Generate overview"
    }

    overview_response = requests.post(
        rival_bot_url,
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
            if decoded.startswith("data:"):
                try:
                    parsed = json.loads(decoded.replace("data: ", ""))
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
        "event": 10,
        "function_id": function_id,
        "prompt": "Generate documentation"
    }

    documentation_response = requests.post(
        rival_bot_url,
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
            if decoded.startswith("data:"):
                try:
                    parsed = json.loads(decoded.replace("data: ", ""))
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
        "what_it_does": final_overview.get("what_it_does", ""),
        "how_it_works": final_overview.get("how_it_works", ""),
        "overview": final_overview.get("what_it_does", ""),
        "strengths": final_overview.get("strengths", []),
        "limitations": final_overview.get("limitations", []),
        "long_description": final_documentation
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

    # =========================================================
    # STEP 7: GENERATE CHANGELOG
    # =========================================================

    changelog_payload = {
        "event": 9,
        "function_id": function_id,
        "prompt": "Generate changelog for the draft version"
    }

    changelog_response = requests.post(
        rival_bot_url,
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
            if decoded.startswith("data:"):
                try:
                    parsed = json.loads(decoded.replace("data: ", ""))
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
            "project-timeline-intelligence-engine"
        )
    )