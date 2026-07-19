import json
import os

from config import DATABASE_FILE


def load_database():

    if not os.path.exists(DATABASE_FILE):

        data = {
            "groups": {}
        }

        save_database(data)

        return data

    with open(DATABASE_FILE, "r", encoding="utf-8") as f:

        data = json.load(f)

    if "groups" not in data:
        data["groups"] = {}
        save_database(data)

    return data


def save_database(data):

    with open(DATABASE_FILE, "w", encoding="utf-8") as f:

        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )


def generate_group_code():

    import random
    import string

    db = load_database()

    while True:

        code = "".join(

            random.choice(
                string.ascii_uppercase +
                string.digits
            )

            for _ in range(6)

        )

        if code not in db["groups"]:
            return code