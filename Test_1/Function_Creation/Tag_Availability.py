from dotenv import load_dotenv
import os

load_dotenv()


def check_tag_availability(name:str):
    token = os.getenv("BEARER_TOKEN")
    org_id = os.getenv("ORG_ID")
    import requests
    import json

    url = "https://cortexone.rival.io/api/v1/tags/check"

    payload = json.dumps({"tags": [name]})
    headers = {
        "X-Organization-ID": org_id,
        "Authorization": f"Bearer {token}"
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    # print(response.text)
    return response.json()
if __name__=='__main__':
    print(check_tag_availability())
# {
#     "success": true,
#     "message": "Tag availability checked",
#     "data": {
#         "tags": [
#             {
#                 "name": "am ghosh",
#                 "available": true
#             }
#         ]
#     }
# }


# if exists

# {"code": "CONFLICT", "message": "Tag conflict", "details": "tags already exist: dao"}
