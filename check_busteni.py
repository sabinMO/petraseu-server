import osmium

class H(osmium.SimpleHandler):

    def node(self, n):
        if n.tags.get("name") == "Bușteni":
            print("NODE")
            print(dict(n.tags))

    def way(self, w):
        if w.tags.get("name") == "Bușteni":
            print("WAY")
            print(dict(w.tags))

handler = H()
handler.apply_file("osm/romania-260716.osm.pbf", locations=False)