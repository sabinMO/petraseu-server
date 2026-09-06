import os
import json
import psycopg2

DATABASE_URL = os.environ.get("DATABASE_URL", "")


def get_connection():
    return psycopg2.connect(DATABASE_URL, sslmode="require")


def init_db():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS petraseu (
                id INTEGER PRIMARY KEY DEFAULT 1,
                data JSONB NOT NULL DEFAULT '{"groups": {}}'
            )
        """)
        cur.execute("""
            INSERT INTO petraseu (id, data)
            VALUES (1, '{"groups": {}}')
            ON CONFLICT (id) DO NOTHING
        """)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"init_db error: {e}")


def load_database():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT data FROM petraseu WHERE id = 1")
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            db = row[0]
            if isinstance(db, str):
                db = json.loads(db)
            if "groups" not in db:
                db["groups"] = {}
            return db
        return {"groups": {}}
    except Exception as e:
        print(f"load_database error: {e}")
        return {"groups": {}}


def save_database(data):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE petraseu SET data = %s WHERE id = 1",
            (json.dumps(data),)
        )
        conn.commit()
        cur.close()
        conn.close()
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


# Initializeaza baza la pornire
init_db()
