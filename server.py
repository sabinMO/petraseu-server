from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid
import string
import random
from datetime import datetime
from database import load_database, save_database
from graphhopper import search_places, build_route

app = Flask(__name__)
CORS(app)


def generate_code():
    db = load_database()
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if code not in db["groups"]:
            return code


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/places/search", methods=["GET"])
def places_search():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"success": False, "results": []})
    results = search_places(query)
    return jsonify({"success": True, "results": results})


@app.route("/route/build", methods=["POST"])
def route_build():
    data = request.get_json()
    points = data.get("points", [])
    if len(points) < 2:
        return jsonify({"success": False, "message": "Minim 2 puncte."})
    route = build_route(points)
    if route is None:
        return jsonify({"success": False, "message": "Nu s-a putut genera traseul."})
    return jsonify({"success": True, "route": route})


@app.route("/groups/create", methods=["POST"])
def create_group():
    data = request.get_json()
    group_name = data.get("group_name", "").strip()
    member_name = data.get("member_name", "").strip()
    if not group_name or not member_name:
        return jsonify({"success": False, "message": "Date incomplete."})
    db = load_database()
    code = generate_code()
    admin_token = str(uuid.uuid4())
    db["groups"][code] = {
        "name": group_name,
        "admin": member_name,
        "admin_token": admin_token,
        "members": {
            member_name: {"lat": None, "lon": None, "online": True}
        },
        "messages": [],
        "route": None,
        "created_at": datetime.now().isoformat()
    }
    save_database(db)
    print(f"[CREATE] Group {code} by {member_name}")
    return jsonify({
        "success": True,
        "group_code": code,
        "group_name": group_name,
        "admin_token": admin_token
    })


@app.route("/groups/join", methods=["POST"])
def join_group():
    data = request.get_json()
    group_code = data.get("group_code", "").strip().upper()
    member_name = data.get("member_name", "").strip()
    if not group_code or not member_name:
        return jsonify({"success": False, "message": "Date incomplete."})
    db = load_database()
    if group_code not in db["groups"]:
        return jsonify({"success": False, "message": "Grupul nu există."})
    group = db["groups"][group_code]
    if member_name in group["members"]:
        group["members"][member_name]["online"] = True
    else:
        group["members"][member_name] = {"lat": None, "lon": None, "online": True}
    save_database(db)
    print(f"[JOIN] {member_name} -> {group_code}")
    return jsonify({"success": True, "group_name": group["name"]})


@app.route("/groups/leave", methods=["POST"])
def leave_group():
    data = request.get_json()
    group_code = data.get("group_code", "").strip().upper()
    member_name = data.get("member_name", "").strip()
    db = load_database()
    if group_code not in db["groups"]:
        return jsonify({"success": False})
    group = db["groups"][group_code]
    if member_name in group["members"]:
        group["members"][member_name]["online"] = False
    save_database(db)
    print(f"[LEAVE] {member_name} -> {group_code}")
    return jsonify({"success": True})


@app.route("/groups/delete", methods=["POST"])
def delete_group():
    data = request.get_json()
    group_code = data.get("group_code", "").strip().upper()
    admin_token = data.get("admin_token", "").strip()
    db = load_database()
    if group_code not in db["groups"]:
        return jsonify({"success": False, "message": "Grupul nu există."})
    group = db["groups"][group_code]
    if group.get("admin_token") != admin_token:
        return jsonify({"success": False, "message": "Nu ești admin."})
    del db["groups"][group_code]
    save_database(db)
    print(f"[DELETE] Group {group_code}")
    return jsonify({"success": True})


@app.route("/locations/<group_code>", methods=["GET"])
def get_locations(group_code):
    group_code = group_code.upper()
    db = load_database()
    if group_code not in db["groups"]:
        return jsonify({"success": False, "message": "Grupul nu există."})
    group = db["groups"][group_code]
    members = []
    for name, data in group["members"].items():
        members.append({
            "name": name,
            "lat": data["lat"],
            "lon": data["lon"],
            "online": data["online"]
        })
    return jsonify({"success": True, "members": members})


@app.route("/locations/<group_code>", methods=["POST"])
def update_location(group_code):
    group_code = group_code.upper()
    data = request.get_json()
    member_name = data.get("member_name", "").strip()
    lat = data.get("lat")
    lon = data.get("lon")
    db = load_database()
    if group_code not in db["groups"]:
        return jsonify({"success": False})
    group = db["groups"][group_code]
    if member_name not in group["members"]:
        return jsonify({"success": False})
    group["members"][member_name]["lat"] = lat
    group["members"][member_name]["lon"] = lon
    group["members"][member_name]["online"] = True
    save_database(db)
    print(f"[UPDATE] {datetime.now().strftime('%H:%M:%S')} {member_name}: {lat}, {lon}")
    return jsonify({"success": True})


@app.route("/chat/<group_code>", methods=["GET"])
def get_messages(group_code):
    group_code = group_code.upper()
    db = load_database()
    if group_code not in db["groups"]:
        return jsonify({"success": False, "messages": []})
    messages = db["groups"][group_code]["messages"]
    return jsonify({"success": True, "messages": messages})


@app.route("/chat/<group_code>", methods=["POST"])
def send_message(group_code):
    group_code = group_code.upper()
    data = request.get_json()
    member_name = data.get("member_name", "").strip()
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"success": False})
    db = load_database()
    if group_code not in db["groups"]:
        return jsonify({"success": False})
    message = {
        "name": member_name,
        "text": text,
        "time": datetime.now().strftime("%H:%M")
    }
    db["groups"][group_code]["messages"].append(message)
    save_database(db)
    return jsonify({"success": True})


@app.route("/route/<group_code>", methods=["GET"])
def get_route(group_code):
    group_code = group_code.upper()
    db = load_database()
    if group_code not in db["groups"]:
        return jsonify({"success": False})
    route = db["groups"][group_code].get("route")
    return jsonify({"success": True, "route": route})


@app.route("/route/<group_code>", methods=["POST"])
def save_route(group_code):
    group_code = group_code.upper()
    data = request.get_json()
    route = data.get("route")
    db = load_database()
    if group_code not in db["groups"]:
        return jsonify({"success": False})
    db["groups"][group_code]["route"] = route
    save_database(db)
    return jsonify({"success": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
