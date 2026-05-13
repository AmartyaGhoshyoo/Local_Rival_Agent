from dotenv import load_dotenv
import os

load_dotenv()

def tags_details():
  token = os.getenv("BEARER_TOKEN")
  org_id = os.getenv("ORG_ID")
  import requests
  import json
  url = "https://cortexone.rival.io/api/v1/tags"

  payload = ""
  headers = {
        "X-Organization-ID": org_id,
        "Authorization": f"Bearer {token}"
    }

  response = requests.request("GET", url, headers=headers, data=payload)
  return response.json()
# print(json.dumps(response.json(), indent=2))


