from config import config
from services.auth.protocols import BaseService
from bs4 import BeautifulSoup
import json


class Service(BaseService):
    def __init__(self):
        super().__init__()
        self._url = config["CTFD"]["URL"].rstrip("/")
        self._user = None
        self._s.headers.update({"Content-Type": "application/json"})

    def fetch_user_info(self, name, access_token):
        self._s.headers.update({"Authorization": f"Bearer {access_token}"})
        r = self._s.get(self.path("/api/v1/users/me"))
        
        # Debug: Log the response status and content type
        print(f"DEBUG CTFd: Status Code: {r.status_code}")
        print(f"DEBUG CTFd: Content-Type: {r.headers.get('Content-Type', 'Not set')}")
        print(f"DEBUG CTFd: Response length: {len(r.content)} bytes")
        
        # Check if response is successful
        if r.status_code != 200:
            print(f"DEBUG CTFd: Non-200 status code. Response text: {r.text[:200]}")
            return None
        
        # Try to parse JSON with error handling
        try:
            json_res = r.json()
        except json.JSONDecodeError as e:
            print(f"DEBUG CTFd: JSON decode error: {e}")
            print(f"DEBUG CTFd: Response text: {r.text[:500]}")
            return None
        except Exception as e:
            print(f"DEBUG CTFd: Unexpected error parsing JSON: {e}")
            return None
        
        # Validate response structure
        if "data" not in json_res:
            print(f"DEBUG CTFd: 'data' key not in response. Keys: {json_res.keys()}")
            return None
        
        # Validate user identity
        if name != json_res["data"]["name"] and name != json_res["data"]["email"]:
            print(f"DEBUG CTFd: Name mismatch. Provided: {name}, Got name: {json_res['data'].get('name')}, email: {json_res['data'].get('email')}")
            return None
        
        print(f"DEBUG CTFd: Successfully fetched user info for {name}")
        return json_res["data"]
