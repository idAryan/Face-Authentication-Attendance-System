"""
Face Authentication Attendance System - Flask application.
Run: python app.py
"""
import base64
from pathlib import Path

import cv2
import numpy as np
from flask import Flask, request, jsonify, render_template, url_for

from config import DATA_DIR
from face_auth import FaceRegistry, FaceIdentifier, SpoofDetector, AttendanceDB

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB

# Shared instances
registry = FaceRegistry()
spoof = SpoofDetector()
identifier = FaceIdentifier(registry=registry, spoof_detector=spoof)
attendance_db = AttendanceDB()


def decode_image_from_request():
    """Decode image from request (JSON base64 or multipart file)."""
    if request.content_type and "application/json" in request.content_type:
        data = request.get_json()
        if not data or "image" not in data:
            return None, "Missing 'image' (base64) in JSON body."
        try:
            b64 = data["image"].split(",")[-1] if "," in data["image"] else data["image"]
            raw = base64.b64decode(b64)
        except Exception as e:
            return None, f"Invalid base64: {e}"
    elif request.files and "image" in request.files:
        f = request.files["image"]
        raw = f.read()
    else:
        return None, "Send image as JSON { \"image\": \"<base64>\" } or multipart form 'image'."
    nparr = np.frombuffer(raw, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return None, "Could not decode image."
    return img, None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register_page():
    if request.method == "GET":
        return render_template("register.html", users=registry.list_users())
    # POST: register from JSON or form
    if request.is_json:
        data = request.get_json() or {}
        user_id = (data.get("user_id") or "").strip()
        name = (data.get("name") or "").strip()
    else:
        user_id = (request.form.get("user_id") or "").strip()
        name = (request.form.get("name") or "").strip()
    if not user_id or not name:
        return jsonify({"success": False, "message": "user_id and name required"}), 400
    img, err = decode_image_from_request()
    if err:
        return jsonify({"success": False, "message": err}), 400
    success, message = registry.register_from_image(img, user_id, name)
    return jsonify({"success": success, "message": message})


@app.route("/attend")
def attend_page():
    return render_template("attend.html")


@app.route("/attendance")
def attendance_page():
    records = attendance_db.get_records(limit=200)
    summary = attendance_db.get_today_summary()
    return render_template("attendance.html", records=records, summary=summary)


# ---------- API ----------

@app.route("/api/users", methods=["GET"])
def api_list_users():
    return jsonify(registry.list_users())


@app.route("/api/users/<user_id>", methods=["DELETE"])
def api_delete_user(user_id):
    if registry.delete_user(user_id):
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "User not found"}), 404


@app.route("/api/identify", methods=["POST"])
def api_identify():
    """Identify face in uploaded image. Optional ?spoof=0 to skip liveness."""
    img, err = decode_image_from_request()
    if err:
        return jsonify({"success": False, "message": err}), 400
    run_spoof = request.args.get("spoof", "1") == "1"
    user_id, name, message, _ = identifier.identify(
        img, run_spoof_check=run_spoof, require_liveness=run_spoof
    )
    return jsonify({
        "success": user_id is not None,
        "user_id": user_id,
        "name": name,
        "message": message,
    })


@app.route("/api/punch-in", methods=["POST"])
def api_punch_in():
    img, err = decode_image_from_request()
    if err:
        return jsonify({"success": False, "message": err}), 400
    user_id, name, message, _ = identifier.identify(img, run_spoof_check=True, require_liveness=True)
    if user_id is None:
        return jsonify({"success": False, "message": message}), 400
    attendance_db.punch_in(user_id, name)
    return jsonify({"success": True, "user_id": user_id, "name": name, "message": f"Punch-in recorded for {name}."})


@app.route("/api/punch-out", methods=["POST"])
def api_punch_out():
    img, err = decode_image_from_request()
    if err:
        return jsonify({"success": False, "message": err}), 400
    user_id, name, message, _ = identifier.identify(img, run_spoof_check=True, require_liveness=True)
    if user_id is None:
        return jsonify({"success": False, "message": message}), 400
    attendance_db.punch_out(user_id, name)
    return jsonify({"success": True, "user_id": user_id, "name": name, "message": f"Punch-out recorded for {name}."})


if __name__ == "__main__":
    DATA_DIR.mkdir(exist_ok=True)
    app.run(host="0.0.0.0", port=5000, debug=True)
