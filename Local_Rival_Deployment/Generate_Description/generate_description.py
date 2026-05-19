from dotenv import load_dotenv
import os
import requests
import json

# =========================
# 🔐 ENV
# =========================
load_dotenv()



# =========================
# 🚀 MAIN FUNCTION
# =========================

def generate_and_save_description(function_slug: str, function_id: str,function_name:str="Amartya"):
    token = os.getenv("BEARER_TOKEN")
    org_id = os.getenv("ORG_ID")
    
    
    headers = {
        "X-Organization-ID": org_id,
        "Authorization": f"Bearer {token}"
    }

    print("\n📝 Generating description...")

    # -------------------------
    # STEP 1: FETCH DETAILS
    # -------------------------
    details_url = f"https://cortexone.rival.io/api/v1/function/agent-foundry/{function_slug}/details"
    details_res = requests.get(details_url, headers=headers).json()

    data = details_res["data"]
    version = data["versions"][0]

    files = version["files"]
    runtime = version["runtime"]

    category_name = data["categories"][0]["name"]
    category_id = data["categories"][0]["category_id"]

    sector_ids = [s["sector_id"] for s in data["sectors"]]
    tag_ids = [t["tag_id"] for t in data["tags"]]
    tags = [t["name"] for t in data["tags"]]

    short_description = data["short_description"]

    # -------------------------
    # STEP 2: GENERATE DESCRIPTION
    # -------------------------
    gen_url = "https://cortexone.rival.io/api/v1/functions/generate-description"

    gen_payload = {
        "tool_name": function_name,
        "runtime": runtime,
        "category_name": category_name,
        "tool_type": runtime,
        "files": files,
        "compute_type": "CPU",
        "tags": tags,
        "short_description": short_description,
        "sectors": sector_ids,
        "events": []
    }

    gen_res = requests.post(
        gen_url,
        headers={**headers, "Content-Type": "application/json"},
        json=gen_payload
    ).json()

    desc = gen_res["data"]

    # -------------------------
    # STEP 3: FORMAT LONG DESCRIPTION
    # -------------------------
    long_description_obj = {
        "what_it_does": desc["what_it_does"],
        "how_it_works": desc["how_it_works"],
        "strengths": [s["value"] for s in desc["strengths"]],
        "limitations": [l["value"] for l in desc["limitations"]],
        "long_description": desc["long_description"]
    }

    long_description_str = json.dumps(long_description_obj)

    # -------------------------
    # STEP 4: SAVE DESCRIPTION
    # -------------------------
    update_url = f"https://cortexone.rival.io/api/v1/function/agent-foundry/{function_slug}/details"

    update_payload = {
        "fnSlug": function_slug,
        "orgSlug": "agent-foundry",
        "function_id": function_id,
        "function_name": function_name,
        "short_description": short_description,
        "long_description": long_description_str,
        "category_ids": [category_id],
        "sector_ids": sector_ids,
        "tag_ids": tag_ids
    }

    update_res = requests.put(
        update_url,
        headers={**headers, "Content-Type": "application/json"},
        json=update_payload
    )

    print("\n✅ Description Saved:")
    print(json.dumps(update_res.json(), indent=2))

    return update_res.json()

if __name__ == "__main__":
    function_slug = "cortexone-acoustic-analysis-handler"  # replace if needed
    function_id = "16cb5efc-fce3-4f10-8b0b-aeb86843c28e"  # replace if needed

    try:
        response = generate_and_save_description(function_slug, function_id,function_name="whatever")
        print("\n🎉 Final Response:")
        print(json.dumps(response, indent=2))

    except Exception as e:
        print("\n❌ Error:", str(e))










# from dotenv import load_dotenv
# import os

# load_dotenv()
# token = os.getenv("BEARER_TOKEN")
# org_id = os.getenv("ORG_ID")

# def generate_and_save_description(function_slug: str, function_id: str):

#     import requests
#     import json

#     headers = {
#         "X-Organization-ID": org_id,
#         "Authorization": f"Bearer {token}"
#     }

#     # STEP 1: GET DETAILS → extract files + metadata
#     details_url = f"https://cortexone.rival.io/api/v1/function/agent-foundry/{function_slug}/details"
#     details_res = requests.request("GET", details_url, headers=headers).json()

#     data = details_res["data"]
#     version = data["versions"][0]

#     files = version["files"]
#     runtime = version["runtime"]

#     category_name = data["categories"][0]["name"]
#     sector_ids = [s["sector_id"] for s in data["sectors"]]
#     tag_ids = [t["tag_id"] for t in data["tags"]]
#     tags = [t["name"] for t in data["tags"]]

#     short_description = data["short_description"]

#     # STEP 2: Generate description
#     gen_url = "https://cortexone.rival.io/api/v1/functions/generate-description"

#     gen_payload = json.dumps({
#         "tool_name": function_slug,
#         "runtime": runtime,
#         "category_name": category_name,
#         "tool_type": runtime,
#         "files": files,
#         "compute_type": "CPU",
#         "tags": tags,
#         "short_description": short_description,
#         "sectors": sector_ids,
#         "events": []
#     })

#     gen_res = requests.request(
#         "POST",
#         gen_url,
#         headers={**headers, "Content-Type": "application/json"},
#         data=gen_payload
#     ).json()

#     desc = gen_res["data"]

#     # STEP 3: Convert to escaped string
#     long_description_obj = {
#         "what_it_does": desc["what_it_does"],
#         "how_it_works": desc["how_it_works"],
#         "strengths": [s["value"] for s in desc["strengths"]],
#         "limitations": [l["value"] for l in desc["limitations"]],
#         "long_description": desc["long_description"]
#     }

#     long_description_str = json.dumps(long_description_obj)

#     # STEP 4: Save details
#     update_url = f"https://cortexone.rival.io/api/v1/function/agent-foundry/{function_slug}/details"

#     update_payload = json.dumps({
#         "fnSlug": function_slug,
#         "orgSlug": "agent-foundry",
#         "function_id": function_id,
#         "function_name": function_slug,
#         "short_description": short_description,
#         "long_description": long_description_str,
#         "category_ids": [data["categories"][0]["category_id"]],
#         "sector_ids": sector_ids,
#         "tag_ids": tag_ids
#     })

#     update_res = requests.request(
#         "PUT",
#         update_url,
#         headers={**headers, "Content-Type": "application/json"},
#         data=update_payload
#     )

#     return update_res.json()


# if __name__ == "__main__":
#     print(generate_and_save_description(
#         function_slug="awsdsadsadda",
#         function_id="53d8fb3a-60e5-4849-8aaa-b30625ada974"
#     ))