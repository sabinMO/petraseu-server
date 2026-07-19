import requests

NOMINATIM = "https://nominatim.openstreetmap.org/search"


def search_place(query):

    q = query.lower().strip()

    extra = ""

    if "gara" in q or "station" in q:
        extra = " railway station"

    elif "cabana" in q:
        extra = " alpine hut"

    elif "vf" in q or "varful" in q or "vârf" in q:
        extra = " peak"

    elif "refugiu" in q:
        extra = " shelter"

    elif "cascada" in q:
        extra = " waterfall"

    search = q + extra

    response = requests.get(

        NOMINATIM,

        params={

            "q": search,
            "format": "jsonv2",
            "limit": 15,
            "addressdetails": 1

        },

        headers={

            "User-Agent": "PeTraseu"

        },

        timeout=20

    )

    data = response.json()

    results = []

    for place in data:

        results.append({

            "name": place["display_name"],
            "lat": float(place["lat"]),
            "lon": float(place["lon"])

        })

    return results