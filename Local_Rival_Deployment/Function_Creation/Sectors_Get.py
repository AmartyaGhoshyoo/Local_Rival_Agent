import requests
from dotenv import load_dotenv
import os

load_dotenv()

def sector_get():
    token = os.getenv("BEARER_TOKEN")
    org_id = os.getenv("ORG_ID")
    url = "https://cortexone.rival.io/api/v1/function/top-sectors"

    payload = ""
    headers = {
            "X-Organization-ID": org_id,
            "Authorization": f"Bearer {token}"
        }

    response = requests.request("GET", url, headers=headers, data=payload)

    return response.json()

if __name__=='__main__':
    print(sector_get())

"""
{
    "sectors": [
        {
            "sector_id": "fd1efcfa-99b2-4ddc-838e-20ee8cea79e7",
            "name": "Technology & Software",
            "slug": ""
        },
        {
            "sector_id": "800db3ed-f8db-4024-aeef-3d2edf4490a8",
            "name": "Data, AI & Analytics",
            "slug": ""
        },
        {
            "sector_id": "d86936a9-89d2-44c8-bf39-d5ead0b5ef67",
            "name": "Media, Marketing & Advertising",
            "slug": ""
        },
        {
            "sector_id": "cb6d839d-779b-421e-9c67-ef2b109a671f",
            "name": "Travel, Transportation & Hospitality",
            "slug": ""
        },
        {
            "sector_id": "7dfea3bc-f564-49ea-a630-f6ad2a88f47c",
            "name": "Healthcare & Life Sciences",
            "slug": ""
        },
        {
            "sector_id": "52298099-4f84-41b8-a991-b5121c2ec9c1",
            "name": "General / Cross-Industry",
            "slug": ""
        },
        {
            "sector_id": "78ed8e6c-888c-44ad-910f-542acfeb1321",
            "name": "Financial Services",
            "slug": ""
        },
        {
            "sector_id": "81306fbd-f4cb-477a-b5b1-d533cd71f4f4",
            "name": "Research & Education",
            "slug": ""
        },
        {
            "sector_id": "83ce1103-8cc4-48e1-ae57-a167628fa798",
            "name": "Government & Public Sector",
            "slug": ""
        },
        {
            "sector_id": "580627e0-692f-4227-ad89-eb99ad393469",
            "name": "Energy & Utilities",
            "slug": ""
        },
        {
            "sector_id": "cf44c455-4185-47b2-ae42-4ac75d1f6be6",
            "name": "Cybersecurity",
            "slug": ""
        },
        {
            "sector_id": "1528dd6b-5c6e-4fe3-92f3-16c0a2d3b1d3",
            "name": "Customer Support & CX",
            "slug": ""
        },
        {
            "sector_id": "6fa9b6f0-ca6e-4798-8a6f-b906d18f314f",
            "name": "Legal & Compliance",
            "slug": ""
        },
        {
            "sector_id": "b45594cb-13ff-4c86-baae-016342d818a5",
            "name": "Operations & Business Productivity",
            "slug": ""
        },
        {
            "sector_id": "1f6735a0-1b98-46f2-b0a3-658d6607302a",
            "name": "Human Resources & People Ops",
            "slug": ""
        },
        {
            "sector_id": "e0807e66-ec4d-47f6-9e2d-fc77d745a54c",
            "name": "Retail & E-Commerce",
            "slug": ""
        },
        {
            "sector_id": "4a26aaa7-4eba-4fd1-be4e-aa656d5bd2a3",
            "name": "Manufacturing & Industrial",
            "slug": ""
        },
        {
            "sector_id": "5bfb58a7-5528-445b-a515-e50292885da7",
            "name": "Web3, Crypto & Blockchain",
            "slug": ""
        },
        {
            "sector_id": "eb619d62-f201-4fd5-a2d2-d88a336646f7",
            "name": "Telecommunications",
            "slug": ""
        }
    ]
}
"""