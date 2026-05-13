import requests

class TokenManager:
    def __init__(self):
        self.session_token = None
        self.refresh_token = None

    def login(self):
        print("🔐 Logging in...")

        url = "https://api.descope.com/v1/auth/password/signin"

        payload = {
            "loginId": "team_agent.foundry@yahoo.com",
            "password": "htM5a!&O25Qw", # ⚠️ Reminder: Secure this later!
            "loginOptions": {}
        }

        # This is your static Project ID
        headers = {
            "Authorization": "Bearer P34ixVh0LRlEd09OkvD4EPsV8Aj4" 
        }

        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            res = response.json()
            self.session_token = res["sessionJwt"]
            self.refresh_token = res["refreshJwt"]
            print("✅ Login successful")
        else:
            print("❌ Login failed!")
            print("Error:", response.text)
            raise Exception("Authentication failed")

    def get_token(self):
        if not self.session_token:
            self.login()
        return self.session_token

    def refresh(self):
        print("🔄 Refreshing token...")

        url = "https://api.descope.com/v1/auth/refresh"

        payload = {
            "refreshJwt": self.refresh_token
        }
        
        # Descope usually requires the Project ID for the refresh endpoint too
        headers = {
            "Authorization": "Bearer P34ixVh0LRlEd09OkvD4EPsV8Aj4" 
        }

        res = requests.post(url, json=payload, headers=headers)

        if res.status_code == 200:
            data = res.json()
            self.session_token = data["sessionJwt"]
            print("✅ Token refreshed")
        else:
            print("⚠️ Refresh failed, logging in again...")
            self.login()


# Initialize the token manager
token_manager = TokenManager()

def safe_request(method, url, **kwargs):
    headers = kwargs.get("headers", {})
    headers["Authorization"] = f"Bearer {token_manager.get_token()}"
    kwargs["headers"] = headers

    response = requests.request(method, url, **kwargs)

    # 🔥 Token expired
    if response.status_code == 401:
        print("⚠️ Token expired")

        token_manager.refresh()

        headers["Authorization"] = f"Bearer {token_manager.get_token()}"
        response = requests.request(method, url, **kwargs)

    return response


def main():
    # 1. Define the endpoint URL
    target_url = "https://cortexone.rival.io/api/v1/users/me"
    
    # 2. Call your wrapper function
    print(f"Fetching data from {target_url}...")
    response = safe_request("GET", target_url)
    
    # 3. Print the results
    print(f"Status Code: {response.status_code}")
    
    try:
        # Attempt to parse and print the JSON response
        data = response.json()
        print("Response Data:", data)
    except Exception:
        # Fallback if the response isn't JSON
        print("Failed to parse JSON. Raw text:", response.text)

if __name__ == "__main__":
    main()