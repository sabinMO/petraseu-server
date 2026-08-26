from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid
import string
import random
from datetime import datetime
from database import db

app = Flask(__name__)
CORS(app)


def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/groups/create", methods=["POST"])
def create_group():
    data = request.get_json()
    group_name = data.get("group_name", "").strip()
    member_name = data.get("member_name", "").strip()

    if not group_name or not member_name:
        return jsonify({"success": False, "message": "Date incomplete."})

    code = generate_code()
    while code in db["groups"]:
        code = generate_code()

    admin_token = str(uuid.uuid4())

    db["groups"][code] = {
        "name": group_name,
        "admin": member_name,
        "admin_token": admin_token,
        "members": {
            member_name: {
                "lat": None,
                "lon": None,
                "online": True
            }
        },
        "messages": [],
        "route": None,
        "created_at": datetime.now().isoformat()
    }

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

    if group_code not in db["groups"]:
        return jsonify({"success": False, "message": "Grupul nu există."})

    group = db["groups"][group_code]

    # Dacă membrul există deja, îl reactivăm în loc să dăm eroare
    if member_name in group["members"]:
        group["members"][member_name]["online"] = True
        print(f"[REJOIN] {member_name} -> {group_code}")
    else:
        group["members"][member_name] = {
            "lat": None,
            "lon": None,
            "online": True
        }
        print(f"[JOIN] {member_name} -> {group_code}")

    return jsonify({
        "success": True,
        "group_name": group["name"]
    })


@app.route("/groups/leave", methods=["POST"])
def leave_group():
    data = request.get_json()
    group_code = data.get("group_code", "").strip().upper()
    member_name = data.get("member_name", "").strip()

    if group_code not in db["groups"]:
        return jsonify({"success": False})

    group = db["groups"][group_code]

    if member_name in group["members"]:
        # Marcam ca offline dar nu stergem
        group["members"][member_name]["online"] = False
        print(f"[LEAVE] {member_name} -> {group_code}")

    return jsonify({"success": True})


@app.route("/groups/delete", methods=["POST"])
def delete_group():
    data = request.get_json()
    group_code = data.get("group_code", "").strip().upper()
    admin_token = data.get("admin_token", "").strip()

    if group_code not in db["groups"]:
        return jsonify({"success": False, "message": "Grupul nu există."})

    group = db["groups"][group_code]

    if group["admin_token"] != admin_token:
        return jsonify({"success": False, "message": "Nu ești admin."})

    del db["groups"][group_code]
    print(f"[DELETE] Group {group_code}")

    return jsonify({"success": True})


@app.route("/locations/<group_code>", methods=["GET"])
def get_locations(group_code):
    group_code = group_code.upper()

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

    if group_code not in db["groups"]:
        return jsonify({"success": False})

    group = db["groups"][group_code]

    if member_name not in group["members"]:
        return jsonify({"success": False})

    group["members"][member_name]["lat"] = lat
    group["members"][member_name]["lon"] = lon
    group["members"][member_name]["online"] = True

    print(f"[UPDATE] {datetime.now().strftime('%H:%M:%S')} "
          f"{member_name}: {lat}, {lon}")

    return jsonify({"success": True})


@app.route("/chat/<group_code>", methods=["GET"])
def get_messages(group_code):
    group_code = group_code.upper()

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

    if group_code not in db["groups"]:
        return jsonify({"success": False})

    message = {
        "name": member_name,
        "text": text,
        "time": datetime.now().strftime("%H:%M")
    }

    db["groups"][group_code]["messages"].append(message)

    return jsonify({"success": True})


@app.route("/route/<group_code>", methods=["GET"])
def get_route(group_code):
    group_code = group_code.upper()

    if group_code not in db["groups"]:
        return jsonify({"success": False})

    route = db["groups"][group_code].get("route")

    return jsonify({"success": True, "route": route})


@app.route("/route/<group_code>", methods=["POST"])
def save_route(group_code):
    group_code = group_code.upper()
    data = request.get_json()
    route = data.get("route")

    if group_code not in db["groups"]:
        return jsonify({"success": False})

    db["groups"][group_code]["route"] = route

    return jsonify({"success": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
