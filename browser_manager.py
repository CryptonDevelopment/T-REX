import requests
import time

class BrowserManager:
    def __init__(self):
        self.api_url = "http://local.adspower.net:50325"

    def start_profile(self, profile_id):
        try:
            url = f"{self.api_url}/api/v1/browser/start?user_id={profile_id}&open_tabs=1&headless=0"
            
            resp = requests.get(url, timeout=10).json()
            
            if resp["code"] == 0:
                ws = resp["data"]["ws"]["puppeteer"]
                print(f"[AdsPower] Profile {profile_id} started. WS: {ws}")
                return ws
            else:
                print(f"[AdsPower] Error starting {profile_id}: {resp.get('msg')}")
                return None
                
        except Exception as e:
            print(f"[AdsPower] Connection error: {e}")
            return None

    def stop_profile(self, profile_id):
        try:
            requests.get(f"{self.api_url}/api/v1/browser/stop?user_id={profile_id}", timeout=5)
        except:
            pass