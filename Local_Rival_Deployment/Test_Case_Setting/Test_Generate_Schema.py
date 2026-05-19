from dotenv import load_dotenv
import os

load_dotenv()


def generate_schema(data:dict):
    token = os.getenv("BEARER_TOKEN")
    org_id = os.getenv("ORG_ID")

    import requests
    import json

    url = "https://cortexone.rival.io/api/app/generate-schema"

    payload =json.dumps(data)

    headers = {
        "X-Organization-ID": org_id,
        "Authorization": f"Bearer {token}"
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    return response.json()


if __name__ == '__main__':
    import json
    data=generate_schema({
        "files": [
            {
                "filename": "cortexone_function.py",
                "content": "import json\nimport pandas as pd\n\n\ndef cortexone_handler(event, context):\n    try:\n        if not isinstance(event, dict):\n            return {\"statusCode\": 400,\"body\": json.dumps({\"error\": \"Invalid input: event must be a dictionary.\"})}\n\n        if \"num\" not in event:\n            return {\"statusCode\": 400,\"body\": json.dumps({\"error\": \"Missing required key: 'num'.\"})}\n\n        nums = event[\"num\"]\n\n        if not isinstance(nums, list):\n            return {\"statusCode\": 400,\"body\": json.dumps({\"error\": \"Invalid input: 'num' must be a list of numbers.\"})}\n\n        if len(nums) == 0:\n            return {\"statusCode\": 400,\"body\": json.dumps({\"error\": \"Invalid input: 'num' must not be empty.\"})}\n\n        try:\n            s = pd.Series(nums, dtype=\"float64\")\n        except (ValueError, TypeError):\n            return {\"statusCode\": 400,\"body\": json.dumps({\"error\": \"Invalid input: 'num' must contain only numeric values.\"})}\n\n        result = {\"sum\": s.sum(), \"mean\": s.mean()}\n\n        return {\"statusCode\": 200,\"body\": json.dumps(result)}\n\n    except Exception as e:\n        return {\"statusCode\": 500,\"body\": json.dumps({\"error\": \"Internal server error\", \"details\": str(e)})}"
            },
            {
                "filename": "requirements.txt",
                "content": "pandas"
            }
        ]
    })
    print(json.dumps(data,indent=2))
    
    
    
# """
# Response from request

# {
#   "schema": [
#     {
#       "id": "generated_event_0",
#       "key": "event",
#       "label": "Event Data",
#       "input": "object",
#       "properties": {
#         "num": {
#           "type": "array"
#         }
#       },
#       "validation": {
#         "required": true
#       },
#       "ui": {
#         "helperText": "Provide the event data as a JSON object."
#       }
#     },
#     {
#       "id": "generated_num_1",
#       "key": "num",
#       "label": "Numbers List",
#       "input": "array",
#       "items": {
#         "type": "number"
#       },
#       "validation": {
#         "required": true,
#         "min": 1
#       },
#       "ui": {
#         "helperText": "Enter a list of numbers."
#       }
#     }
#   ]
# }


# """    