from dotenv import load_dotenv
import os
import requests
from .ai_generate_requirements import generate_requirements

load_dotenv()



def save_function_version(function_id, code_str):
    token = os.getenv("BEARER_TOKEN")
    org_id = os.getenv("ORG_ID")


    requirements_txt = generate_requirements(code_str)

    url = f"https://cortexone.rival.io/api/v1/functions/{function_id}/save-version"

    payload = {
        "files": [
            {
                "path": "/cortexone_function.py",
                "meta": {
                    "name": "cortexone_function.py",
                    "mime": "text/x-python"
                },
                "data": code_str
            },
            {
                "path": "/requirements.txt",
                "meta": {
                    "name": "requirements.txt",
                    "mime": "text/plain"
                },
                "data": requirements_txt
            }
        ],
        "version": "Draft"
    }

    headers = {
        "X-Organization-ID": org_id,
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    response = requests.put(url, headers=headers, json=payload)
    return response.json()