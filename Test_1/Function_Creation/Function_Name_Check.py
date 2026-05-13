from dotenv import load_dotenv
import os

load_dotenv()

def function_name_check(name:str):
  token = os.getenv("BEARER_TOKEN")
  org_id = os.getenv("ORG_ID")

  import requests
  import json

  url = "https://cortexone.rival.io/api/v1/functions/check"

  payload = json.dumps({
    "function_name": name
  })
  headers = {
        "X-Organization-ID": org_id,
        "Authorization": f"Bearer {token}"
    }

  response = requests.request("POST", url, headers=headers, data=payload)

  
  return response.json()
if __name__=='__main__':
    print(function_name_check("whatever"))


# { "success": true, "message": "Tool name availability checked", "data": { "available": true, "message": "Function name is available" } }

# {
#     "success": true,
#     "message": "Tool name availability checked",
#     "data": {
#         "available": false,
#         "message": "Function name is already taken"
#     }
# }