import requests
from config import GITHUB_TOKEN, GIST_ID

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

URL = f"https://api.github.com/gists/{GIST_ID}"


def load_database():
    try:
        r = requests.get(URL, headers=HEADERS, timeout=10)
        data = r.json()
        content = data["files"]["petraseu_db.json"]["content"]
        import json
        db = json.loads(content)
        if "groups" not in db:
            db["groups"] = {}
        return db
    except Exception as e:
        print(f"load_database error: {e}")
        return {"groups": {}}


def save_database(data):
    try:
        import json
        requests.patch(
            URL,
            headers=HEADERS,
            json={"files": {"petraseu_db.json": {"content": json.dumps(data)}}},
            timeout=10
        )
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
