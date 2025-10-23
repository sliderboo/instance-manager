#!/usr/bin/env python3
import os
import sys
import requests
import base64


def main(url, bot_token, username=None, password=None):
    if not os.path.exists("instance.yml"):
        print("instance.yml not found")
        exit(0)
    config = open("instance.yml", "r").read()
    enc_config = base64.b64encode(config.encode()).decode()
    data = {
        "config": enc_config,
    }
    if username and password:
        data.update({"creds": {"username": username, "password": password}})
    r = requests.post(
        f"{url}/api/challenge/init",
        headers={"Authorization": f"Bearer {bot_token}"},
        json=data,
    )
    if r.status_code < 200 and r.status_code > 300:
        print(r.text)
        exit(1)
    r = r.json()
    print(r)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: deploy.py <url> <bot_token>")
        exit(0)
    elif len(sys.argv) == 3:
        main(sys.argv[1], sys.argv[2])
    elif len(sys.argv) < 5:
        print("Usage: deploy.py <url> <bot_token> <username> <password>")
        exit(0)
    else:
        main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])