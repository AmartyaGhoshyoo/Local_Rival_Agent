import requests
import os
from dotenv import load_dotenv, set_key

# Load environment variables when the module starts
load_dotenv()

class TokenManager:
    def __init__(self):
        self.env_file = ".env"
        # Pull initially from the environment
        self.session_token = os.getenv("BEARER_TOKEN")
        self.refresh_token = os.getenv("REFRESH_TOKEN")

    def login(self):
        print("🔐 Logging in to Descope...")
        url = "https://api.descope.com/v1/auth/password/signin"
        payload = {
            "loginId": "team_agent.foundry@yahoo.com",
            "password": "htM5a!&O25Qw", 
            "loginOptions": {}
        }
        headers = {
            "Authorization": "Bearer P34ixVh0LRlEd09OkvD4EPsV8Aj4" 
        }
        
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            res = response.json()
            self.session_token = res["sessionJwt"]
            self.refresh_token = res["refreshJwt"]
            self.save_and_export_tokens()
            print("✅ Login successful")
        else:
            raise Exception(f"Authentication failed: {response.text}")

    def refresh(self):
        if not self.refresh_token:
            self.login()
            return

        print("🔄 Refreshing token...")
        url = "https://api.descope.com/v1/auth/refresh"
        payload = {"refreshJwt": self.refresh_token}
        headers = {"Authorization": "Bearer P34ixVh0LRlEd09OkvD4EPsV8Aj4"}

        res = requests.post(url, json=payload, headers=headers)
        if res.status_code == 200:
            data = res.json()
            self.session_token = data["sessionJwt"]
            self.save_and_export_tokens()
            print("✅ Token refreshed successfully")
        else:
            print("⚠️ Refresh failed, logging in again...")
            self.login()

    def save_and_export_tokens(self):
        # 1. Update active memory so FastAPI child threads see the new token immediately
        os.environ["BEARER_TOKEN"] = self.session_token
        if self.refresh_token:
            os.environ["REFRESH_TOKEN"] = self.refresh_token

        # 2. Update .env file for future server restarts
        set_key(self.env_file, "BEARER_TOKEN", self.session_token)
        if self.refresh_token:
            set_key(self.env_file, "REFRESH_TOKEN", self.refresh_token)

        # 3. Print export command to the terminal running FastAPI
        print("\n" + "="*60)
        print("⚠️ NEW TOKEN GENERATED. TERMINAL EXPORT COMMAND:")
        print(f"export BEARER_TOKEN='{self.session_token}'")
        print("="*60 + "\n")

    def ensure_valid_token(self):
        """Runs a pre-flight check before your agent starts."""
        print("🔍 Checking token validity...")
        if not self.session_token:
            self.login()
            return
        
        # Lightweight check to CortexOne
        check_url = "https://cortexone.rival.io/api/v1/users/me"
        headers = {"Authorization": f"Bearer {self.session_token}"}
        res = requests.get(check_url, headers=headers)

        if res.status_code == 401:
            print("⚠️ Token expired detected before agent run.")
            self.refresh()
        else:
            print("✅ Token is still valid.")

# Initialize a global instance for the app
token_manager = TokenManager()
if __name__=="__main__":
    token_manager.ensure_valid_token() 