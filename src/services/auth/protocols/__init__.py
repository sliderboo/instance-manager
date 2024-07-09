import requests


class BaseService:
    def __init__(self):
        self._s = requests.Session()

    def path(self, path):
        return self._url + path

    def fetch_user_info(self, name, password):
        pass
