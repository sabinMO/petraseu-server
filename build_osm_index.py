import json
import osmium


class HikingHandler(osmium.SimpleHandler):

    def __init__(self):
        super().__init__()
        self.results = []

    def add(self, tags, lat, lon):

        name = tags.get("name")

        if not name:
            return

        self.results.append({
            "name": name,
            "lat": lat,
            "lon": lon,
            "tags": dict(tags)
        })

    def node(self, n):

        tags = n.tags

        if (
            tags.get("railway") in ("station", "halt") or
            tags.get("tourism") in ("alpine_hut", "wilderness_hut") or
            tags.get("natural") == "peak" or
            tags.get("waterway") == "waterfall" or
            tags.get("amenity") == "shelter" or
            tags.get("place") in ("city", "town", "village", "hamlet")
        ):
            self.add(tags, n.location.lat, n.location.lon)


handler = HikingHandler()

handler.apply_file("osm/romania-260716.osm.pbf", locations=True)

with open("osm/index.json", "w", encoding="utf8") as f:
    json.dump(handler.results, f, ensure_ascii=False)

print("Total puncte:", len(handler.results))