import requests
import time

from config import JSONBIN_API_KEY, JSONBIN_BIN_ID


HEADERS = {
    "X-Master-Key": JSONBIN_API_KEY,
    "Content-Type": "application/json"
}

URL = f"https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}"

TIMEOUT = 15
RETRIES = 3

# Cache local în memoria procesului Render.
# Este folosit doar pentru a proteja baza împotriva
# unor erori temporare de conexiune la JSONBin.
_cached_database = None


def _empty_database():
    return {
        "groups": {}
    }


def load_database():
    """
    Încarcă baza de date din JSONBin.

    IMPORTANT:
    O eroare de conexiune NU este tratată ca o bază goală.
    Dacă avem o copie în cache, o folosim.
    Dacă nu avem cache, returnăm baza goală doar la prima pornire,
    dar marcăm eroarea prin print.
    """

    global _cached_database

    last_error = None

    for attempt in range(1, RETRIES + 1):

        try:
            print(
                f"[DATABASE] Loading JSONBin "
                f"(attempt {attempt}/{RETRIES})"
            )

            response = requests.get(
                URL,
                headers=HEADERS,
                timeout=TIMEOUT
            )

            print(
                f"[DATABASE] JSONBin GET status: "
                f"{response.status_code}"
            )

            response.raise_for_status()

            data = response.json()

            db = data.get("record")

            if not isinstance(db, dict):
                raise ValueError(
                    "JSONBin nu contine un record valid."
                )

            if "groups" not in db:
                db["groups"] = {}

            _cached_database = db

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
                time.sleep(2)

    # --------------------------------------------------
    # JSONBin nu a putut fi accesat.
    # NU considerăm asta o bază goală.
    # --------------------------------------------------

    if _cached_database is not None:

        print(
            "[DATABASE] JSONBin unavailable. "
            "Using cached database."
        )

        return _cached_database

    print(
        "[DATABASE] CRITICAL: JSONBin unavailable "
        "and no cached database exists."
    )

    print(
        f"[DATABASE] Last error: {last_error}"
    )

    # La prima pornire, dacă JSONBin nu poate fi accesat,
    # returnăm o bază goală pentru ca serverul să poată porni.
    #
    # IMPORTANT:
    # save_database() NU va salva această bază goală
    # dacă nu provine dintr-un load valid.
    return _empty_database()


def save_database(data):
    """
    Salvează baza de date în JSONBin.

    Verifică efectiv răspunsul serverului.
    """

    global _cached_database

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

    # Protecție importantă:
    # nu permitem salvarea unei baze goale peste una existentă
    # doar pentru că JSONBin a avut temporar o problemă.
    if len(data["groups"]) == 0 and _cached_database is not None:

        if len(_cached_database.get("groups", {})) > 0:

            print(
                "[DATABASE] WARNING: refusing to overwrite "
                "existing database with EMPTY database."
            )

            return False

    last_error = None

    for attempt in range(1, RETRIES + 1):

        try:

            print(
                f"[DATABASE] Saving JSONBin "
                f"(attempt {attempt}/{RETRIES})"
            )

            response = requests.put(
                URL,
                json=data,
                headers=HEADERS,
                timeout=TIMEOUT
            )

            print(
                f"[DATABASE] JSONBin PUT status: "
                f"{response.status_code}"
            )

            response.raise_for_status()

            # Verificăm dacă răspunsul este JSON valid.
            result = response.json()

            if not isinstance(result, dict):
                raise ValueError(
                    "Raspuns JSONBin invalid."
                )

            _cached_database = data

            print(
                f"[DATABASE] Saved successfully. "
                f"Groups: {len(data['groups'])}"
            )

            return True

        except Exception as e:

            last_error = e

            print(
                f"[DATABASE] Save attempt "
                f"{attempt}/{RETRIES} failed: {e}"
            )

            if attempt < RETRIES:
                time.sleep(2)

    print(
        f"[DATABASE] CRITICAL: could not save database: "
        f"{last_error}"
    )

    return False
