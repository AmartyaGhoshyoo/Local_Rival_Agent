import os
import requests
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
BASE_URL = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}"

def send_text_message(to_number: str, text: str):
    """Sends a standard text message to the user."""
    url = f"{BASE_URL}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": text},
    }
    requests.post(url, headers=headers, json=payload)

def send_pdf_document(to_number: str, file_path: str):
    """Uploads a local PDF to WhatsApp and sends it to the user."""
    # Step 1: Upload the file to Meta's servers
    upload_url = f"{BASE_URL}/media"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    
    with open(file_path, 'rb') as f:
        files = {
            'file': ('Resume.pdf', f, 'application/pdf'),
            'type': (None, 'document'),
            'messaging_product': (None, 'whatsapp')
        }
        upload_res = requests.post(upload_url, headers=headers, files=files)
    
    media_id = upload_res.json().get("id")
    if not media_id:
        print("🚨 Failed to upload media to WhatsApp:", upload_res.text)
        return

    # Step 2: Send a message containing the media ID
    send_url = f"{BASE_URL}/messages"
    send_headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "document",
        "document": {
            "id": media_id,
            "filename": "Your_Professional_Resume.pdf",
            "caption": "Here is your generated resume! Best of luck. 🎉"
        }
    }
    requests.post(send_url, headers=send_headers, json=payload)