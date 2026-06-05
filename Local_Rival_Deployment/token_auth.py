import requests
import os
from pathlib import Path
from dotenv import load_dotenv, set_key

# Load environment variables when the module starts
load_dotenv()

class TokenManager:
    def __init__(self):
        # 🌟 Calculate absolute paths based on the file structure in your screenshot
        current_dir = Path(__file__).resolve().parent             # Local_Rival_Deployment
        root_dir = current_dir.parent                             # AI_PROJECT folder
        
        self.local_env_file = current_dir / ".env"
        self.whatsapp_env_file = root_dir / "WhatsApp_Rival_Agent" / ".env"

        # Pull initially from the environment
        self.session_token = os.getenv("BEARER_TOKEN")
        self.refresh_token = os.getenv("REFRESH_TOKEN")
        print(f"🔄 Initialized TokenManager. Session Token loaded: {bool(self.session_token)}")

    def login(self):
        print("🔑 Attempting to login and fetch new tokens...")
        url = "https://api.descope.com/v1/auth/password/signin"
        payload = {
            "loginId": "team_agent.foundry@yahoo.com",
            "password": "htM5a!&O25Qw", 
            # "loginId": "b22cs002@nitm.ac.in",
            # "password": "tarzen@#123@#Amartya",
            "loginOptions": {}
        }
        headers = {
            "Authorization": "Bearer P34ixVh0LRlEd09OkvD4EPsV8Aj4" 
        }
        
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            print("✅ Login successful! Extracting tokens...")
            res = response.json()
            self.session_token = res["sessionJwt"]
            self.refresh_token = res["refreshJwt"]
            self.save_and_export_tokens()
        else:
            print(f"🚨 Login failed! Status Code: {response.status_code}")
            raise Exception(f"Authentication failed: {response.text}")

    def refresh(self):
        print("♻️ Attempting to refresh token...")
        if not self.refresh_token:
            print("⚠️ No refresh token found. Falling back to login.")
            self.login()
            return

        url = "https://api.descope.com/v1/auth/refresh"
        payload = {"refreshJwt": self.refresh_token}
        headers = {"Authorization": "Bearer P34ixVh0LRlEd09OkvD4EPsV8Aj4"}

        res = requests.post(url, json=payload, headers=headers)
        if res.status_code == 200:
            print("✅ Token refreshed successfully!")
            data = res.json()
            self.session_token = data["sessionJwt"]
            self.save_and_export_tokens()
        else:
            print(f"🚨 Refresh failed (Status: {res.status_code}). Falling back to full login.")
            self.login()

    def save_and_export_tokens(self):
        print("💾 Saving and exporting tokens to active memory and BOTH .env files...")
        
        # 1. Update active memory so FastAPI child threads see the new token immediately
        os.environ["BEARER_TOKEN"] = self.session_token
        if self.refresh_token:
            os.environ["REFRESH_TOKEN"] = self.refresh_token

        # 2. Update WhatsApp_Rival_Agent/.env 
        if self.whatsapp_env_file.exists():
            set_key(str(self.whatsapp_env_file), "BEARER_TOKEN", self.session_token)
            if self.refresh_token:
                set_key(str(self.whatsapp_env_file), "REFRESH_TOKEN", self.refresh_token)
            print(f"✅ Updated WhatsApp .env: {self.whatsapp_env_file.name}")

        # 3. Update Local_Rival_Deployment/.env 
        if self.local_env_file.exists():
            set_key(str(self.local_env_file), "BEARER_TOKEN", self.session_token)
            if self.refresh_token:
                set_key(str(self.local_env_file), "REFRESH_TOKEN", self.refresh_token)
            print(f"✅ Updated Local Deployment .env: {self.local_env_file.name}")

    def ensure_valid_token(self):
        """Runs a pre-flight check before your agent starts."""
        print("🛡️ Running pre-flight token check...")
        if not self.session_token:
            print("⚠️ No session token found in memory. Initiating login sequence.")
            self.login()
            return
        
        # Lightweight check to CortexOne
        check_url = "https://cortexone.rival.io/api/v1/users/me"
        headers = {"Authorization": f"Bearer {self.session_token}"}
        res = requests.get(check_url, headers=headers)
        
        if res.status_code == 401:
            print("⚠️ Session token is expired or invalid (401 Unauthorized). Triggering refresh.")
            self.refresh()
        elif res.status_code == 200:
            print("✅ Token is valid! Ready to make API calls.")
        else:
            print(f"❓ Unexpected status during token check: {res.status_code}. Response: {res.text}")

# Initialize a global instance for the app
token_manager = TokenManager()

if __name__=="__main__":
    print("\n🚀 Starting direct execution of TokenManager script...")
    token_manager.ensure_valid_token() 
    print("🏁 TokenManager execution complete!\n")