from flask import Flask, request, jsonify
from flask_cors import CORS
from search import search_place
from osm_search import search_place

import json
import os
import random
import string
from datetime import datetime

import requests

from config import GRAPHHOPPER_API_KEY

app = Flask(__name__)
CORS(app)

DATABASE_FILE = "database.json"

OVERPASS_URL = "https://overpass.kumi.systems/api/interpreter"
GRAPHHOPPER_ROUTE_URL = "https://graphhopper.com/api/1/route"


# ===============================
# DATABASE
# ===============================

def load_database():

    if not os.path.exists(DATABASE_FILE):

        save_database({
            "groups": {}
        })

    with open(DATABASE_FILE, "r", encoding="utf-8") as f:

        db = json.load(f)

    if "groups" not in db:

        db["groups"] = {}
        save_database(db)

    return db


def save_database(data):

    with open(DATABASE_FILE, "w", encoding="utf-8") as f:

        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )


# ===============================
# HELPERS
# ===============================

def generate_group_code():

    db = load_database()

    while True:

        code = "".join(

            random.choice(
                string.ascii_uppercase +
                string.digits
            )

            for _ in range(6)

        )

        if code not in db["groups"]:
            return code


import requests
import json

def cauta_locatie_overpass(query, lat_centru=45.4, lon_centru=25.0, raza_km=100):
    """
    Caută POI-uri în OSM prin Overpass API.
    Funcționează pentru gări, cabane, refugii, vârfuri, etc.
    """
    
    # Mapare termeni românești → taguri OSM
    TIPURI_OSM = {
        "gara": [("railway", "station"), ("railway", "halt")],
        "gară": [("railway", "station"), ("railway", "halt")],
        "cabana": [("tourism", "alpine_hut"), ("tourism", "wilderness_hut"), ("amenity", "shelter")],
        "cabană": [("tourism", "alpine_hut"), ("tourism", "wilderness_hut")],
        "refugiu": [("tourism", "wilderness_hut"), ("amenity", "shelter")],
        "varf": [("natural", "peak")],
        "vârf": [("natural", "peak")],
        "lac": [("natural", "water"), ("natural", "lake")],
        "cascada": [("waterway", "waterfall")],
        "cascadă": [("waterway", "waterfall")],
    }
    
    raza_grade = raza_km / 111.0
    bbox = f"{lat_centru - raza_grade},{lon_centru - raza_grade},{lat_centru + raza_grade},{lon_centru + raza_grade}"
    
    # Detectează tipul din query
    query_lower = query.lower()
    tip_detectat = None
    nume_fara_tip = query
    
    for cuvant, taguri in TIPURI_OSM.items():
        if query_lower.startswith(cuvant + " "):
            tip_detectat = taguri
            nume_fara_tip = query[len(cuvant):].strip()
            break
    
    # Construiește query Overpass
    parts = []
    
    if tip_detectat:
        # Căutare specifică cu tip OSM + nume
        for tag_key, tag_val in tip_detectat:
            parts.append(f'node["{tag_key}"="{tag_val}"][~"name"~"{nume_fara_tip}",i]({bbox});')
            parts.append(f'way["{tag_key}"="{tag_val}"][~"name"~"{nume_fara_tip}",i]({bbox});')
    else:
        # Căutare generală pe nume
        parts.append(f'node[~"name"~"{query}",i]({bbox});')
        parts.append(f'way[~"name"~"{query}",i]({bbox});')
    
    overpass_query = f"""
    [out:json][timeout:10];
    (
      {''.join(parts)}
    );
    out center 10;
    """
    
    try:
        print(overpass_query)
        r = requests.post(
            "https://overpass-api.de/api/interpreter",
             data={
                 "data": overpass_query
             },
             timeout=20
)
        
        print(r.request.headers)
        print(r.request.body)
        print("STATUS:", r.status_code)
        print(r.text[:1000])
        r.raise_for_status()
        data = r.json()
        print(data)
        rezultate = []
        for el in data.get("elements", []):
            name = el.get("tags", {}).get("name", "")
            if not name:
                continue
            
            if el["type"] == "node":
                lat, lon = el["lat"], el["lon"]
            else:
                lat = el.get("center", {}).get("lat")
                lon = el.get("center", {}).get("lon")
            
            if lat and lon:
                rezultate.append({
                    "name": name,
                    "lat": lat,
                    "lon": lon,
                    "tip": el.get("tags", {}).get("railway") or 
                           el.get("tags", {}).get("tourism") or
                           el.get("tags", {}).get("natural", "")
                })

        print("REZULTATE:", rezultate)
        
        return rezultate
        
    except Exception as e:
        return []


def cauta_locatie_combinat(query, lat=45.4, lon=25.0):
    """
    Strategie în două etape:
    1. Încearcă Photon (rapid, bun pentru orașe și adrese)
    2. Dacă rezultate slabe, încearcă Overpass (bun pentru POI-uri specifice)
    """
    
    # Etapa 1: Photon
    try:
        r = requests.get(
            "https://photon.komoot.io/api/",
            params={"q": query, "limit": 5, "lat": lat, "lon": lon},
            timeout=6
        )
        rezultate_photon = []
        for el in r.json().get("features", []):
            coord = el["geometry"]["coordinates"]
            prop = el["properties"]
            rezultate_photon.append({
                "name": prop.get("name", query),
                "lat": coord[1],
                "lon": coord[0]
            })
        
        # Dacă Photon a găsit ceva relevant, returnează
        #if len(rezultate_photon) >= 2:
            #return rezultate_photon
    except:
        pass
    
    # Etapa 2: Overpass pentru POI-uri specifice
    return cauta_locatie_overpass(query, lat, lon)


def graphhopper_search(query):
    return cauta_locatie_combinat(query)


# ===============================
# CREATE GROUP
# ===============================

@app.post("/groups/create")
def create_group():

    data = request.get_json()

    group_name = data.get("group_name", "").strip()
    organizer_name = data.get("organizer_name", "").strip()

    if group_name == "" or organizer_name == "":

        return jsonify({

            "success": False,
            "message": "Completează toate câmpurile."

        })

    db = load_database()

    code = generate_group_code()

    db["groups"][code] = {

        "code": code,

        "name": group_name,

        "created_at": datetime.now().isoformat(),

        "members": [

            {

                "name": organizer_name,
                "lat": None,
                "lon": None,
                "online": True

            }

        ],

        "messages": [],

        "route": None

    }

    save_database(db)

    return jsonify({

        "success": True,
        "group_code": code

    })


# ===============================
# JOIN GROUP
# ===============================

@app.post("/groups/join")
def join_group():

    data = request.get_json()

    code = data.get("group_code", "").upper().strip()
    member_name = data.get("member_name", "").strip()

    db = load_database()

    if code not in db["groups"]:

        return jsonify({

            "success": False,
            "message": "Grupul nu există."

        })

    group = db["groups"][code]

    for member in group["members"]:

        if member["name"].lower() == member_name.lower():

            return jsonify({

                "success": False,
                "message": "Există deja un membru cu acest nume."

            })

    group["members"].append({

        "name": member_name,
        "lat": None,
        "lon": None,
        "online": True

    })

    save_database(db)

    return jsonify({

        "success": True,
        "group_name": group["name"]

    })


# ===============================
# GROUP DETAILS
# ===============================

@app.get("/groups/<code>")
def get_group(code):

    db = load_database()

    code = code.upper()

    if code not in db["groups"]:

        return jsonify({

            "success": False,
            "message": "Grup inexistent."

        })

    return jsonify({

        "success": True,
        "group": db["groups"][code]

    })



# ===============================
# SEARCH PLACES
# ===============================

@app.get("/places/search")
def search_places():

 query = request.args.get("q", "").strip()

 if not query:
    return jsonify([])

 return jsonify(search_place(query))


# ===============================
# BUILD ROUTE
# ===============================

@app.post("/route/build")
def build_route():

    data = request.get_json()

    points = data.get("points", [])

    if len(points) < 2:
        return jsonify({
            "success": False,
            "message": "Sunt necesare minim două puncte."
        })

    params = []

    for point in points:
        params.append(
            ("point", f"{point['lat']},{point['lon']}")
        )

    params.extend([
        ("profile", "foot"),
        ("locale", "ro"),
        ("instructions", "true"),
        ("points_encoded", "false"),
        ("calc_points", "true"),
        ("key", GRAPHHOPPER_API_KEY)
    ])

    try:

        response = requests.get(
            GRAPHHOPPER_ROUTE_URL,
            params=params,
            timeout=30
        )

        data = response.json()

        if "paths" not in data:

            print("========== GRAPHHOPPER ==========")
            print(data)
            print("=================================")

            return jsonify({
                "success": False,
                "message": str(data)
            })

        return jsonify({
            "success": True,
            "route": data["paths"][0]
        })

    except Exception as e:

        print(e)

        return jsonify({
            "success": False,
            "message": str(e)
        })

# ===============================
# SAVE ROUTE
# ===============================

@app.post("/route/save")
def save_route():

    data = request.get_json()

    code = data.get("group_code", "").upper()

    route = data.get("route")

    db = load_database()

    if code not in db["groups"]:

        return jsonify({

            "success": False

        })

    db["groups"][code]["route"] = route

    save_database(db)

    return jsonify({

        "success": True

    })


# ===============================
# GET ROUTE
# ===============================

@app.get("/route/<code>")
def get_route(code):

    db = load_database()

    code = code.upper()

    if code not in db["groups"]:

        return jsonify({

            "success": False

        })

    return jsonify({

        "success": True,
        "route": db["groups"][code].get("route")

    })


# ===============================
# UPDATE LOCATION
# ===============================

@app.post("/location/update")
def update_location():

    data = request.get_json()

    code = data.get("group_code", "").upper()

    member_name = data.get("member_name", "")

    lat = data.get("lat")

    lon = data.get("lon")

    db = load_database()

    if code not in db["groups"]:

        return jsonify({

            "success": False

        })

    members = db["groups"][code]["members"]

    for member in members:

        if member["name"] == member_name:

            member["lat"] = lat
            member["lon"] = lon

            save_database(db)

            return jsonify({

                "success": True

            })

    return jsonify({

        "success": False

    })


# ===============================
# SEND MESSAGE
# ===============================

@app.post("/chat/send")
def send_message():

    data = request.get_json()

    code = data.get("group_code", "").upper()
    sender = data.get("sender", "")
    message = data.get("message", "").strip()

    if message == "":

        return jsonify({

            "success": False,
            "message": "Mesaj gol."

        })

    db = load_database()

    if code not in db["groups"]:

        return jsonify({

            "success": False

        })

    db["groups"][code]["messages"].append({

        "sender": sender,
        "message": message,
        "time": datetime.now().strftime("%H:%M")

    })

    save_database(db)

    return jsonify({

        "success": True

    })


# ===============================
# GET CHAT
# ===============================

@app.get("/chat/<code>")
def get_chat(code):

    db = load_database()

    code = code.upper()

    if code not in db["groups"]:

        return jsonify({

            "success": False

        })

    return jsonify({

        "success": True,
        "messages": db["groups"][code]["messages"]

    })


# ===============================
# GET MEMBER LOCATIONS
# ===============================

@app.get("/locations/<code>")
def get_locations(code):

    db = load_database()

    code = code.upper()

    if code not in db["groups"]:

        return jsonify({

            "success": False

        })

    members = []

    for member in db["groups"][code]["members"]:

        members.append({

            "name": member["name"],
            "lat": member["lat"],
            "lon": member["lon"],
            "online": member.get("online", True)

        })

    return jsonify({

        "success": True,
        "members": members

    })


# ===============================
# DEBUG
# ===============================

@app.get("/groups")
def all_groups():

    db = load_database()

    return jsonify(db["groups"])


# ===============================
# START SERVER
# ===============================

if __name__ == "__main__":

    app.run(

        host="0.0.0.0",
        port=5000,
        debug=True

    )