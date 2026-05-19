from dotenv import load_dotenv
import os

load_dotenv()



def function_creation(payload_passed: dict):
    token = os.getenv("BEARER_TOKEN")
    org_id = os.getenv("ORG_ID")
    import requests

    url = "https://cortexone.rival.io/api/v1/functions"

    # payload = {'function_name': ' sadsdsadsadasd',
    # 'short_description': ' dasdsadsadsadsad',
    # 'runtime': ' python:3.13',
    # 'type': ' function',
    # 'category_ids': ' 4c6166e9-9ea2-447a-ae4a-27362ab87bad',
    # 'sector_ids': ' 83ce1103-8cc4-48e1-ae57-a167628fa798',
    # 'compute_type': ' CPU',
    # 'tag_ids':'74705997-44dc-4270-a8c9-b17608d1c187,b1bc42da-e761-4702-9948-f0e7e0e397d4'}
    payload = payload_passed
    headers = {"X-Organization-ID": org_id, "Authorization": f"Bearer {token}"}

    response = requests.request("POST", url, headers=headers, data=payload)

    return response.json()


if __name__ == "__main__":

    print(
        function_creation(
            {
                "function_name": "AI Testing 2",
                "short_description": "AI Testing 2 AI Testing 2 AI Testing 2 AI Testing 2",
                "runtime": "python:3.13",
                "type": "function",
                "category_ids": "4c6166e9-9ea2-447a-ae4a-27362ab87bad",
                "sector_ids": "83ce1103-8cc4-48e1-ae57-a167628fa798",
                "compute_type": "CPU",
                "tag_ids": [
                    "74705997-44dc-4270-a8c9-b17608d1c187",
                    "b1bc42da-e761-4702-9948-f0e7e0e397d4",
                ],
            }
        )
    )


{
    "success": True,
    "message": "Function created successfully",
    "data": {
        "function": {
            "function_id": "fd9bf398-e987-4bef-92bb-7ea1adfe8bea",
            "organization_id": "2b227103-7a6a-4430-8370-e70a3f6bb1f0",
            "user_id": "918a575c-735d-4602-be02-887b3656081f",
            "function_name": "AI Testing 2",
            "short_description": "AI Testing 2 AI Testing 2 AI Testing 2 AI Testing 2",
            "long_description": "",
            "category_ids": ["4c6166e9-9ea2-447a-ae4a-27362ab87bad"],
            "visibility": "private",
            "created_at": "2026-04-05T08:42:45.155302Z",
            "updated_at": "2026-04-05T08:42:45.155302Z",
            "versions": [
                {
                    "version": "",
                    "runtime": "python:3.13",
                    "compute_type": "CPU",
                    "max_memory": 128,
                    "max_runtime": 300,
                    "cpu_limit": 2,
                    "handler": "cortexone_function.cortexone_handler",
                    "files": [
                        {
                            "path": "/cortexone_function.py",
                            "meta": {
                                "name": "cortexone_function.py",
                                "mime": "text/x-python",
                            },
                            "data": 'import json\nimport pandas as pd\n\n\ndef cortexone_handler(event, context):\n    try:\n        if not isinstance(event, dict):\n            return {\n                "statusCode": 400,\n                "body": json.dumps({"error": "Invalid input: event must be a dictionary."}),\n            }\n\n        if "num" not in event:\n            return {\n                "statusCode": 400,\n                "body": json.dumps({"error": "Missing required key: \'num\'."}),\n            }\n\n        nums = event["num"]\n\n        if not isinstance(nums, list):\n            return {\n                "statusCode": 400,\n                "body": json.dumps({"error": "Invalid input: \'num\' must be a list of numbers."}),\n            }\n\n        if len(nums) == 0:\n            return {\n                "statusCode": 400,\n                "body": json.dumps({"error": "Invalid input: \'num\' must not be empty."}),\n            }\n\n        try:\n            s = pd.Series(nums, dtype="float64")\n        except (ValueError, TypeError):\n            return {\n                "statusCode": 400,\n                "body": json.dumps({"error": "Invalid input: \'num\' must contain only numeric values."}),\n            }\n\n        result = {\n            "sum": s.sum(),\n            "mean": s.mean(),\n        }\n\n        print(f"Sum: {result[\'sum\']}, Mean: {result[\'mean\']}")\n\n        return {\n            "statusCode": 200,\n            "body": json.dumps(result),\n        }\n\n    except Exception as e:\n        return {\n            "statusCode": 500,\n            "body": json.dumps({"error": "Internal server error", "details": str(e)}),\n        }',
                        },
                        {
                            "path": "/requirements.txt",
                            "meta": {"name": "requirements.txt", "mime": "text/plain"},
                            "data": "pandas",
                        },
                    ],
                    "environment": None,
                    "state": "draft",
                    "created_at": "2026-04-05T08:42:45.155302Z",
                    "updated_at": "2026-04-05T08:42:45.155302Z",
                    "event_id": "",
                    "changelog": None,
                    "event_name": "",
                    "event_data": None,
                    "events": None,
                    "visibility": "private",
                    "digital_asset_id": "",
                    "is_deprecated": False,
                    "days_left": None,
                    "uses_digital_assets": False,
                    "makes_external_calls": False,
                }
            ],
            "icon_url": "",
            "organization_email": "agent.foundry@yahoo.com",
            "organization_profile_picture": "https://storage.googleapis.com/rival-data/organizations-Picture/1773288089082933898_cropped-logo.png",
            "type": "function",
            "is_deprecated": False,
        },
        "function_slug": "ai-testing-2",
        "organization_slug": "agent-foundry",
        "sectors": ["83ce1103-8cc4-48e1-ae57-a167628fa798"],
        "uploaded_url": "",
    },
}
