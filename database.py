import os
import time

from supabase import create_client, Client


# --------------------------------------------------
# SUPABASE
# --------------------------------------------------

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL:
    raise RuntimeError("Lipseste SUPABASE_URL")

if not SUPABASE_KEY:
    raise RuntimeError("Lipseste SUPABASE_KEY")


supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


TABLE_NAME = "app_database"
DATABASE_ID = 1

RETRIES = 3
RETRY_DELAY = 2


# --------------------------------------------------
# BAZA GOALA
# --------------------------------------------------

def _empty_database():
    return {
        "groups": {}
    }


# --------------------------------------------------
# LOAD
# --------------------------------------------------

def load_database():

    last_error = None

    for attempt in range(1, RETRIES + 1):

        try:

            print(
                f"[DATABASE] Loading Supabase "
                f"(attempt {attempt}/{RETRIES})"
            )

            response = (
                supabase
                .table(TABLE_NAME)
                .select("data")
                .eq("id", DATABASE_ID)
                .single()
                .execute()
            )

            data = response.data

            if not data:
                raise ValueError(
                    "Supabase nu a returnat date."
                )

            db = data.get("data")

            if not isinstance(db, dict):
                raise ValueError(
                    "Datele din Supabase nu sunt un obiect valid."
                )

            if "groups" not in db:
                db["groups"] = {}

            print(
                f"[DATABASE] Loaded successfully. "
                f"Groups: {len(db['groups'])}"
            )

            return db

        except Exception as e:

            last_error = e

            print(
                f"[DATABASE] Load attempt "
                f"{attempt}/{RETRIES} failed: {e}"
            )

            if attempt < RETRIES:
                time.sleep(RETRY_DELAY)


    print(
        f"[DATABASE] CRITICAL: "
        f"Supabase unavailable: {last_error}"
    )

    # FOARTE IMPORTANT:
    # Nu mai returnam automat o baza goala daca Supabase cade.
    # Altfel putem pierde grupurile.

    raise RuntimeError(
        "Supabase nu poate fi accesat. "
        "Baza de date NU va fi inlocuita cu una goala."
    )


# --------------------------------------------------
# SAVE
# --------------------------------------------------

def save_database(data):

    if not isinstance(data, dict):
        print(
            "[DATABASE] Refusing to save invalid database."
        )
        return False

    if "groups" not in data:
        print(
            "[DATABASE] Refusing to save database "
            "without 'groups'."
        )
        return False


    for attempt in range(1, RETRIES + 1):

        try:

            print(
                f"[DATABASE] Saving Supabase "
                f"(attempt {attempt}/{RETRIES})"
            )

            response = (
                supabase
                .table(TABLE_NAME)
                .update({
                    "data": data
                })
                .eq("id", DATABASE_ID)
                .execute()
            )

            if not response.data:
                raise ValueError(
                    "Supabase nu a confirmat salvarea."
                )

            print(
                f"[DATABASE] Saved successfully. "
                f"Groups: {len(data['groups'])}"
            )

            return True

        except Exception as e:

            print(
                f"[DATABASE] Save attempt "
                f"{attempt}/{RETRIES} failed: {e}"
            )

            if attempt < RETRIES:
                time.sleep(RETRY_DELAY)


    print(
        "[DATABASE] CRITICAL: "
        "could not save database to Supabase."
    )

    return False
