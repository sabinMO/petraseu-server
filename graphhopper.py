import requests

from config import GRAPHHOPPER_API_KEY, OPENROUTESERVICE_API_KEY


# ---------------------------------------------------------
# GraphHopper - doar pentru căutarea locurilor
# ---------------------------------------------------------

GEOCODE_URL = "https://graphhopper.com/api/1/geocode"


# ---------------------------------------------------------
# OpenRouteService / HeiGIT - trasee montane
# ---------------------------------------------------------

ROUTE_URL = (
    "https://api.heigit.org/"
    "openrouteservice/v2/directions/foot-hiking"
)


def search_places(text, limit=10):

    try:

        response = requests.get(
            GEOCODE_URL,
            params={
                "q": text,
                "locale": "ro",
                "country": "RO",
                "limit": limit,
                "key": GRAPHHOPPER_API_KEY
            },
            timeout=15
        )

        response.raise_for_status()

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

        print("GEOCODING ERROR:", e)

        return []


def build_route(points):

    try:

        if len(points) < 2:
            print("ROUTE ERROR: minimum 2 points required")
            return None

        # ORS așteaptă coordonatele în ordinea:
        # [longitude, latitude]
        coordinates = []

        for point in points:

            lat = point.get("lat")
            lon = point.get("lon")

            if lat is None or lon is None:
                continue

            coordinates.append([
                lon,
                lat
            ])

        if len(coordinates) < 2:
            print("ROUTE ERROR: not enough valid coordinates")
            return None

        payload = {
            "coordinates": coordinates,

            "instructions": True,

            "instructions_format": "text",

            "language": "ro",

            "geometry": True,

            "geometry_format": "geojson"
        }

        headers = {
            "Authorization": OPENROUTESERVICE_API_KEY,
            "Content-Type": "application/json"
        }

        print(
            "[ROUTE] Requesting hiking route from "
            "OpenRouteService..."
        )

        response = requests.post(
            ROUTE_URL,
            json=payload,
            headers=headers,
            timeout=60
        )

        print(
            "[ROUTE] ORS status:",
            response.status_code
        )

        response.raise_for_status()

        data = response.json()

        if "features" not in data or not data["features"]:

            print(
                "[ROUTE] ORS returned no route:",
                data
            )

            return None

        feature = data["features"][0]

        geometry = feature.get("geometry", {})

        route_coordinates = geometry.get(
            "coordinates",
            []
        )

        if not route_coordinates:

            print(
                "[ROUTE] Route contains no coordinates."
            )

            return None

        # -------------------------------------------------
        # Convertim răspunsul ORS într-un format apropiat
        # de cel pe care îl folosea aplicația ta.
        #
        # ORS:
        # [lon, lat]
        #
        # Aplicația ta folosește:
        # {"coordinates": [[lon, lat], ...]}
        # -------------------------------------------------

        summary = feature.get(
            "properties",
            {}
        ).get(
            "summary",
            {}
        )

        distance = summary.get(
            "distance",
            0
        )

        duration = summary.get(
            "duration",
            0
        )

        return {
            "points": {
                "coordinates": route_coordinates
            },

            "distance": distance,

            "time": duration,

            "instructions": feature.get(
                "properties",
                {}
            ).get(
                "segments",
                []
            )
        }

    except requests.exceptions.HTTPError as e:

        print(
            "[ROUTE] HTTP ERROR:",
            e
        )

        try:
            print(
                "[ROUTE] Server response:",
                response.text
            )
        except Exception:
            pass

        return None

    except Exception as e:

        print(
            "[ROUTE] ERROR:",
            e
        )

        return None
