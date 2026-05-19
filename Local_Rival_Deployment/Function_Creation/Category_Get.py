import requests

from dotenv import load_dotenv
import os

load_dotenv()
def category_get():
    token = os.getenv("BEARER_TOKEN")
    org_id = os.getenv("ORG_ID")
    url = "https://cortexone.rival.io/api/v1/function/top-categories"

    payload = ""
    headers = {
            "X-Organization-ID": org_id,
            "Authorization": f"Bearer {token}"
        }

    response = requests.request("GET", url, headers=headers, data=payload)

    return response.json()

if __name__=='__main__':
    import json
    print(json.dumps(category_get(),indent=2))
    data=json.loads(category_get())
    print(data['categories'][:2])

"""
{
    "categories": [
        {
            "category_id": "f771f225-fffb-450a-977f-c1d23d8d94d8",
            "name": "Developer Tools",
            "description": "",
            "functions_count": 291
        },
        {
            "category_id": "b04a27d5-61d9-4b69-bc89-b0526f981193",
            "name": "AI & ML",
            "description": "",
            "functions_count": 208
        },
        {
            "category_id": "32632b62-3a86-4b9d-bf30-903f58d0cbad",
            "name": "Data & Analytics",
            "description": "",
            "functions_count": 149
        },
        {
            "category_id": "a38f309f-4581-4714-ad71-a715e9f71c97",
            "name": "Business Intelligence",
            "description": "",
            "functions_count": 90
        },
        {
            "category_id": "fee770ed-f3e1-4695-970f-19857d6bf677",
            "name": "Web & APIs",
            "description": "",
            "functions_count": 77
        },
        {
            "category_id": "9a58f5b7-2152-475c-9ce8-06779616fd93",
            "name": "Security & Compliance",
            "description": "",
            "functions_count": 77
        },
        {
            "category_id": "8eab49a8-5c2f-4348-96b7-3ea2e47db781",
            "name": "Agents & Workflows",
            "description": "",
            "functions_count": 76
        },
        {
            "category_id": "87bc27ab-4a1c-48bb-893e-8bd89d7d2e08",
            "name": "Utilities",
            "description": "",
            "functions_count": 70
        },
        {
            "category_id": "4c6166e9-9ea2-447a-ae4a-27362ab87bad",
            "name": "Data Processing",
            "description": "",
            "functions_count": 67
        },
        {
            "category_id": "778e6c45-ba98-4fd0-b940-a1ea671a3c2c",
            "name": "Productivity",
            "description": "",
            "functions_count": 60
        },
        {
            "category_id": "afe93702-0847-43e6-8582-24f0883db16d",
            "name": "Text & NLP",
            "description": "",
            "functions_count": 59
        },
        {
            "category_id": "3cd4393c-6faa-409a-8706-0fd3600cde2b",
            "name": "Auth & Security",
            "description": "",
            "functions_count": 34
        },
        {
            "category_id": "c9fa11f0-6fbc-4264-aa9b-5c771d4ed9e3",
            "name": "Testing, QA & Validation",
            "description": "",
            "functions_count": 27
        },
        {
            "category_id": "967acf78-6883-4700-8f33-f6caa63456bb",
            "name": "Math, Stats & Optimization",
            "description": "",
            "functions_count": 24
        },
        {
            "category_id": "0fe69717-625f-4925-a31b-1318aab7d3ad",
            "name": "Databases & Storage",
            "description": "",
            "functions_count": 23
        },
        {
            "category_id": "4f84b121-8308-4c83-b397-4135ebec6d97",
            "name": "Integrations",
            "description": "",
            "functions_count": 20
        },
        {
            "category_id": "1462da64-b348-4b9e-9fd3-459311928ff1",
            "name": "Images",
            "description": "",
            "functions_count": 17
        },
        {
            "category_id": "67492cb5-ede7-499e-9e2a-f6cdf4651ce0",
            "name": "Audio & Speech",
            "description": "",
            "functions_count": 15
        },
        {
            "category_id": "e3718dd9-5d2e-4960-b27d-ca0156737992",
            "name": "MCP Server",
            "description": "",
            "functions_count": 11
        }
    ]
}

"""