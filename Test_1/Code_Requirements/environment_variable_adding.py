from dotenv import load_dotenv
import os
import requests
import json
import re
def to_kebab_case(name):
    # lowercase
    name = name.lower()
    
    # replace underscores with space
    name = name.replace("_", " ")
    
    # replace non-alphanumeric with dash
    name = re.sub(r'[^a-z0-9]+', '-', name)
    
    # remove leading/trailing dashes
    return name.strip('-')
load_dotenv()


def add_environment_variable(function_slug, env_keys):
    token = os.getenv("BEARER_TOKEN")
    org_id = os.getenv("ORG_ID")

    url = f"https://cortexone.rival.io/api/v1/function/agent-foundry/{function_slug}/environment-variables"


    payload = {
        "environment_keys": [
    "9140ed62-61b4-4b33-850c-7f458a7a612a"
  ]

    }

    headers = {
        "X-Organization-ID": org_id,
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    response = requests.post(url, headers=headers, json=payload)

    print("\n🌱 Env Response:", json.dumps(response.json(), indent=2))

    return response.json()


if __name__=='__main__':
    name="pediatric-sleep-regression-analyzer"
    name=f"{name}-1"
    print(name)
    data=add_environment_variable(name,"NONE")
    print(json.dumps(data,indent=2))