import json
import unicodedata

with open("osm/index.json", encoding="utf8") as f:
    OSM_INDEX = json.load(f)


def normalize(text):
    text = text.lower()

    text = "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )

    return text


def cauta_locatie_overpass(query):

    q = normalize(query)

    q = q.replace("gara ", "")
    q = q.replace("gara", "")
    q = q.replace("gară ", "")
    q = q.replace("cabana ", "")
    q = q.replace("cabană ", "")
    q = q.replace("varful ", "")
    q = q.replace("vârful ", "")
    q = q.replace("varf ", "")
    q = q.replace("vârf ", "")

    q = q.strip()

    rezultate = []

    for loc in OSM_INDEX:

        nume = normalize(loc["name"])

        if q in nume:

            afisare = loc["name"]

            tags = loc.get("tags", {})

            if tags.get("railway") == "station":
                afisare = "Gara " + afisare

            elif tags.get("tourism") == "alpine_hut":
                afisare = "Cabana " + afisare

            elif tags.get("natural") == "peak":
                afisare = "Vârful " + afisare

            rezultate.append({

                "name": afisare,
                "lat": loc["lat"],
                "lon": loc["lon"]

            })

    rezultate.sort(key=lambda x: len(x["name"]))

    return rezultate[:20]

def search_place(query, limit=10):
    return cauta_locatie_overpass(query)[:limit]