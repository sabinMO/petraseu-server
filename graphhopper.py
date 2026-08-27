import requests

from config import GRAPHHOPPER_API_KEY


GEOCODE_URL = "https://graphhopper.com/api/1/geocode"
ROUTE_URL = "https://graphhopper.com/api/1/route"


def search_places(text, limit=10):

    try:

        response = requests.get(

            GEOCODE_URL,

            params={
                "q": text,
                "locale": "ro",
                "country": "RO",
                "limit": 10,
                "key": GRAPHHOPPER_API_KEY
            },

            timeout=15

        )

        data = response.json()

        results = []

        for hit in data.get("hits", []):

            name = hit.get("name", "")

            city = hit.get("city", "")

            country = hit.get("country", "")

            label = name

            if city:
                label += ", " + city

            if country:
                label += ", " + country

            point = hit.get("point", {})

            results.append({

                "name": label,

                "lat": point.get("lat"),

                "lon": point.get("lng")

            })

        return results

    except Exception as e:

        print(e)

        return []


def build_route(points):
    try:
        params = []
        for point in points:
            params.append(
                ("point", f"{point['lat']},{point['lon']}")
            )
        params.extend([
            ("profile", "hike"),
            ("locale", "ro"),
            ("points_encoded", "false"),
            ("instructions", "true"),
            ("calc_points", "true"),
            ("key", GRAPHHOPPER_API_KEY)
        ])
        response = requests.get(
            ROUTE_URL,
            params=params,
            timeout=30
        )
        data = response.json()
        if "paths" not in data:
            print("GRAPHHOPPER ERROR:", data)
            return None
        path = data["paths"][0]
        return path
    except Exception as e:
        print(e)
        return None
