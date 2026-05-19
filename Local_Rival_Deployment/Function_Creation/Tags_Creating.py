from dotenv import load_dotenv
import os

load_dotenv()

def tags_creation(name:str):
  token = os.getenv("BEARER_TOKEN")
  org_id = os.getenv("ORG_ID")
  import requests
  import json

  url = "https://cortexone.rival.io/api/v1/tags"

  payload = json.dumps({
    "tags": [
      name
    ]
  })
  headers = {
        "X-Organization-ID": org_id,
        'Content-Type': 'application/json',
        "Authorization": f"Bearer {token}"
    }


  response = requests.request("POST", url, headers=headers, data=payload)

  return response.json()
if __name__=='__main__':
  print(tags_creation())

# {
#     "success": true,
#     "message": "Tags created successfully",
#     "data": [
#         {
#             "tag_id": "0bf2196e-d66d-4c54-8137-370c35ceaf0e",
#             "name": "lol",
#             "created_at": "2026-04-02T20:45:09.854768817Z"
#         }
#     ]
# }