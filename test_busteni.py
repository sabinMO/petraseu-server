import osmium

class Test(osmium.SimpleHandler):

    def node(self, n):
        if n.tags.get("name") and "bust" in n.tags.get("name").lower():
            print("NODE:", n.tags.get("name"), dict(n.tags))

    def way(self, w):
        if w.tags.get("name") and "bust" in w.tags.get("name").lower():
            print("WAY:", w.tags.get("name"), dict(w.tags))

    def relation(self, r):
        if r.tags.get("name") and "bust" in r.tags.get("name").lower():
            print("REL:", r.tags.get("name"), dict(r.tags))

handler = Test()
handler.apply_file("osm/romania-260716.osm.pbf", locations=False)