import requests
from config import JSONBIN_API_KEY, JSONBIN_BIN_ID

HEADERS = {
    "X-Master-Key": JSONBIN_API_KEY,
    "Content-Type": "application/json"
}

URL = f"https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}"


def load_database():
    try:
        r = requests.get(URL, headers=HEADERS, timeout=10)
        data = r.json()
        db = data.get("record", {})
        if "groups" not in db:
            db["groups"] = {}
        return db
    except Exception as e:
        print(f"load_database error: {e}")
        return {"groups": {}}


def save_database(data):
    try:
        requests.put(URL, json=data, headers=HEADERS, timeout=10)
    except Exception as e:
        print(f"save_database error: {e}")


def generate_group_code():
    import random
    import string
    db = load_database()
    while True:
        code = "".join(
            random.choice(string.ascii_uppercase + string.digits)
            for _ in range(6)
        )
        if code not in db["groups"]:
            return code
