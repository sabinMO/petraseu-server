import os
import requests

from config import GRAPHHOPPER_API_KEY


# ---------------------------------------------------------
# GraphHopper - cautare locuri
# ---------------------------------------------------------

GEOCODE_URL = "https://graphhopper.com/api/1/geocode"


# ---------------------------------------------------------
# OpenRouteService - trasee
# ---------------------------------------------------------

ORS_ROUTE_URL = (
    "https://api.heigit.org/openrouteservice/v2/"
    "directions/foot-hiking"
)

ORS_API_KEY = os.getenv("ORS_API_KEY")


# ---------------------------------------------------------
# Cautare locuri
# ---------------------------------------------------------

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

            lat = point.get("lat")
            lon = point.get("lng")

            if lat is None or lon is None:
                continue

            results.append({
                "name": label,
                "lat": lat,
                "lon": lon
            })

        print(
            f"[GEOCODE] Found {len(results)} places "
            f"for '{text}'"
        )

        return results

    except Exception as e:

        print(f"[GEOCODE ERROR] {e}")

        return []


# ---------------------------------------------------------
# Decodare Google/ORS Encoded Polyline
# ---------------------------------------------------------

def decode_polyline(encoded):

    coordinates = []
    index = 0
    lat = 0
    lon = 0

    length = len(encoded)

    try:

        while index < length:

            shift = 0
            result = 0

            while True:
                byte = ord(encoded[index]) - 63
                index += 1
                result |= (byte & 0x1F) << shift
                shift += 5
                if byte < 0x20:
                    break

            if result & 1:
                lat_change = ~(result >> 1)
            else:
                lat_change = result >> 1

            lat += lat_change

            shift = 0
            result = 0

            while True:
                byte = ord(encoded[index]) - 63
                index += 1
                result |= (byte & 0x1F) << shift
                shift += 5
                if byte < 0x20:
                    break

            if result & 1:
                lon_change = ~(result >> 1)
            else:
                lon_change = result >> 1

            lon += lon_change

            coordinates.append([
                lon / 100000.0,
                lat / 100000.0
            ])

        return coordinates

    except Exception as e:

        print(f"[POLYLINE ERROR] {e}")

        return []


# ---------------------------------------------------------
# Construire traseu montan
# ---------------------------------------------------------

def build_route(points):

    if not points or len(points) < 2:
        print("[ROUTE] Need at least 2 points.")
        return None

    try:

        print(
            "[ROUTE] Requesting hiking route "
            "from OpenRouteService..."
        )

        coordinates = []

        for point in points:

            lat = point.get("lat")
            lon = point.get("lon")

            if lat is None or lon is None:
                print("[ROUTE] Invalid point:", point)
                return None

            coordinates.append([
                float(lon),
                float(lat)
            ])

        payload = {
            "coordinates": coordinates,
            "language": "ro",
            "geometry": True,
            "instructions": True,
            "instructions_format": "text",
            # Activeaza elevation pentru urcare/coborare
            "elevation": True
        }

        headers = {
            "Authorization": ORS_API_KEY,
            "Content-Type": "application/json"
        }

        response = requests.post(
            ORS_ROUTE_URL,
            json=payload,
            headers=headers,
            timeout=60
        )

        print(f"[ROUTE] ORS status: {response.status_code}")

        if response.status_code != 200:
            print("[ROUTE] HTTP ERROR:", response.text)
            return None

        data = response.json()

        routes = data.get("routes")

        if not routes:
            print("[ROUTE] ORS returned no routes:", data)
            return None

        route = routes[0]

        summary = route.get("summary", {})

        encoded_geometry = route.get("geometry")

        if not encoded_geometry:
            print("[ROUTE] ORS route has no geometry.")
            return None

        coordinates_decoded = decode_polyline(encoded_geometry)

        if not coordinates_decoded:
            print("[ROUTE] Could not decode route geometry.")
            return None

        distance = summary.get("distance", 0)

        # ORS returneaza duration in secunde
        # il convertim in milisecunde pentru compatibilitate
        duration_sec = summary.get("duration", 0)
        duration_ms = int(duration_sec * 1000)

        # ORS returneaza ascent/descent direct in summary
        ascend = round(summary.get("ascent", 0))
        descend = round(summary.get("descent", 0))

        print(
            f"[ROUTE] Route generated. "
            f"Distance: {distance / 1000:.2f} km, "
            f"Duration: {duration_sec / 60:.0f} min, "
            f"Ascent: {ascend} m, "
            f"Descent: {descend} m"
        )

        print(f"[ROUTE] Geometry points: {len(coordinates_decoded)}")

        result = {
            "points": {
                "coordinates": coordinates_decoded
            },
            "distance": distance,
            "time": duration_ms,
            "ascend": ascend,
            "descend": descend,
            "segments": route.get("segments", [])
        }

        print("[ROUTE] Returning route to application.")

        return result

    except requests.exceptions.Timeout:
        print("[ROUTE] OpenRouteService timeout.")
        return None

    except requests.exceptions.RequestException as e:
        print(f"[ROUTE] HTTP request error: {e}")
        return None

    except Exception as e:
        print(f"[ROUTE] Unexpected error: {e}")
        return None
