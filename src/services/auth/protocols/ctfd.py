from config import config
from services.auth.protocols import BaseService
from bs4 import BeautifulSoup


class Service(BaseService):
    def __init__(self):
        super().__init__()
        self._url = config["CTFD"]["URL"].rstrip("/")
        self._user = None
        self._s.headers.update({"Content-Type": "application/json"})

    def fetch_user_info(self, name, access_token):
        self._s.headers.update({"Authorization": f"Bearer {access_token}"})
        r = self._s.get(self.path("/api/v1/users/me"))
        json_res = r.json()
        if "data" not in json_res:
            return None
        if name != json_res["data"]["name"] and name != json_res["data"]["email"]:
            return None
        return json_res["data"]
