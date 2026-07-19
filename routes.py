from flask import Blueprint, request, jsonify

from database import load_database, save_database
from graphhopper import search_places, build_route

routes_bp = Blueprint("routes", __name__)


# ===================================================
# Căutare locații
# ===================================================

@routes_bp.get("/places/search")
def places_search():

    text = request.args.get("q", "").strip()

    if text == "":
        return jsonify([])

    return jsonify(search_places(text))


# ===================================================
# Construire traseu
# ===================================================

@routes_bp.post("/routes/build")
def route_build():

    data = request.get_json()

    points = data.get("points", [])

    if len(points) < 2:

        return jsonify({

            "success": False,
            "message": "Sunt necesare minim două puncte."

        })

    route = build_route(points)

    if route is None:

        return jsonify({

            "success": False,
            "message": "GraphHopper nu a putut calcula traseul."

        })

    return jsonify({

        "success": True,
        "route": route

    })


# ===================================================
# Salvare traseu în grup
# ===================================================

@routes_bp.post("/routes/save")
def save_route():

    data = request.get_json()

    code = data.get("group_code", "").upper()
    route = data.get("route")

    db = load_database()

    if code not in db["groups"]:

        return jsonify({

            "success": False,
            "message": "Grup inexistent."

        })

    db["groups"][code]["route"] = route

    save_database(db)

    return jsonify({

        "success": True

    })


# ===================================================
# Citire traseu
# ===================================================

@routes_bp.get("/routes/<code>")
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