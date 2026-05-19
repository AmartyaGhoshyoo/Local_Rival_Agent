import os
import requests
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
TO = os.getenv("WHATSAPP_TEST_TO")  # e.g. +919876543210 (digits only for API)

if not ACCESS_TOKEN or not PHONE_NUMBER_ID or not TO:
    raise SystemExit("Set ACCESS_TOKEN, PHONE_NUMBER_ID, and WHATSAPP_TEST_TO in .env")

url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json",
}

data = {
    "messaging_product": "whatsapp",
    "to": TO.replace(" ", ""),
    "type": "text",
    "text": {"body": "Hello from Rival Agentic bot"},
}

response = requests.post(url, headers=headers, json=data, timeout=60)
print(response.json())
