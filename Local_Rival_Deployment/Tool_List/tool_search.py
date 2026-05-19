from dotenv import load_dotenv
import os

load_dotenv()



def extended_search():
    token = os.getenv("BEARER_TOKEN")
    org_id = os.getenv("ORG_ID")
    import requests
    import json

    url = "https://cortexone.rival.io/api/v1/extanded_search?limit=3&offset=0"

    payload = {
        "search_in": {
            "digital_assets": False,
            "functions": True
        },
        "query": "",
        "category_ids": [],
        "compute_type": [],
        "sector_ids": [],
        "tag_ids": [],
        "runtime": [],
        "type": [],
        "created_by": [],
        "access_level": [],
        "visibility": [
            "public"
        ],
        "level": [],
        "price": []
    }

    headers = {
        "X-Organization-ID": org_id,
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.request(
        "POST",
        url,
        headers=headers,
        data=json.dumps(payload)
    )

    return response.json()


if __name__ == "__main__":
    import json
    print(
        json.dumps(
            extended_search(),
            indent=2
        )
    )