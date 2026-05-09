# api.py
# Flask REST API for the Conference Management application.
# Exposes all ConferenceDB features as JSON endpoints, plus a Matplotlib chart.
# Run: python api.py  (listens on http://localhost:5000)
# author: Kyra Menai Hamilton

import io

from flask import Flask, jsonify, request, send_file
from flask_cors import CORSimport io

import sys
import os

# ── Matplotlib must use a non-interactive backend before any other import ──
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ── Import ConferenceDB from main.py (same directory) ──
sys.path.insert(0, os.path.dirname(__file__))
from main import ConferenceDB

# ── App setup ──
app = Flask(__name__)
CORS(app)   # Allow the web_ui.html (file://) to call localhost:5000

# ── Database connection ──
db = ConferenceDB(
    mysql_host="localhost",
    mysql_user="root",
    mysql_password="YOUR_MYSQL_PASSWORD",   # CHANGE THIS
    mysql_database="appdbproj",
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="YOUR_NEO4J_PASSWORD"    # CHANGE THIS
)

# ══════════════════════
# 1. Speakers & Sessions
# GET /api/speakers?name=<search_string>
# ══════════════════════
@app.route("/api/speakers", methods=["GET"])
def get_speakers():
    name = request.args.get("name", "").strip()
    rows, err = db.search_speakers(name)
    if err:
        return jsonify({"error": err}), 404
    result = [
        {"speaker": r[0], "session": r[1], "room": r[2]}
        for r in rows
    ]
    return jsonify(result), 200


# ══════════════════════
# 2. Attendees by Company
# GET /api/attendees/<company_id>
# ══════════════════════
@app.route("/api/attendees/<int:company_id>", methods=["GET"])
def get_attendees(company_id):
    company_name, rows, err = db.search_attendees_by_company(company_id)
    if err:
        # company_name is set when company exists but has no attendees
        body = {"error": err}
        if company_name:
            body["company"] = company_name
        return jsonify(body), 404
    result = [
        {
            "name":    r[0],
            "dob":     str(r[1]),   # datetime.date → "YYYY-MM-DD"
            "session": r[2],
            "speaker": r[3],
            "room":    r[4]
        }
        for r in rows
    ]
    return jsonify({"company": company_name, "attendees": result}), 200


# ══════════════════════
# 3. Add New Attendee
# POST /api/attendee
# Body (JSON): { attendee_id, name, dob, gender, company_id }
# ══════════════════════
@app.route("/api/attendee", methods=["POST"])
def add_attendee():
    data       = request.get_json(force=True)
    attendee_id = str(data.get("attendee_id", "")).strip()
    name        = str(data.get("name",        "")).strip()
    dob         = str(data.get("dob",         "")).strip()
    gender      = str(data.get("gender",      "")).strip().title()
    company_id  = str(data.get("company_id",  "")).strip()

    ok, msg = db.add_new_attendee(attendee_id, name, dob, gender, company_id)
    if ok:
        return jsonify({"message": msg}), 201
    return jsonify({"error": msg}), 400

# ══════════════════════
# 4. View Connected Attendees
# GET /api/connections/<attendee_id>
# ══════════════════════
@app.route("/api/connections/<int:attendee_id>", methods=["GET"])
def get_connections(attendee_id):
    name, rows, err = db.view_connected_attendees(attendee_id)
    if err:
        return jsonify({"error": err}), 404
    connections = (
        [{"id": r[0], "name": r[1]} for r in rows]
        if rows else []
    )
    return jsonify({"name": name, "connections": connections}), 200

# ══════════════════════
# 5. Add Attendee Connection
# POST /api/connections
# Body (JSON): { attendee1_id, attendee2_id }
# ══════════════════════
@app.route("/api/connections", methods=["POST"])
def add_connection():
    data = request.get_json(force=True)
    raw1 = str(data.get("attendee1_id", "")).strip()
    raw2 = str(data.get("attendee2_id", "")).strip()

    if not (raw1.isdigit() and raw2.isdigit()):
        return jsonify({"error": "*** ERROR *** Attendee IDs must be numbers"}), 400

    ok, msg = db.add_attendee_connection(int(raw1), int(raw2))
    if ok:
        return jsonify({"message": msg}), 201
    return jsonify({"error": msg}), 400

# ══════════════════════
# 6. View Rooms  (cached — new rooms won't appear until API restarts)
# GET /api/rooms
# ══════════════════════
@app.route("/api/rooms", methods=["GET"])
def get_rooms():
    rows, err = db.view_rooms()
    if err:
        return jsonify({"error": err}), 404
    result = [
        {"id": r[0], "name": r[1], "capacity": r[2]}
        for r in rows
    ]
    return jsonify(result), 200

# ══════════════════════
# 6b. Room Capacity Chart (Matplotlib to PNG)
# GET /api/rooms/chart
# ══════════════════════
@app.route("/api/rooms/chart", methods=["GET"])
def get_rooms_chart():
    rows, err = db.view_rooms()
    if err:
        return jsonify({"error": err}), 404

    # Rooms are already ordered by capacity DESC from the DB
    names      = [r[1] for r in rows]
    capacities = [r[2] for r in rows]

    # Colour-code bars by capacity tier
    def bar_color(cap):
        if cap >= 200: return "#22c55e"    # green  — large
        if cap >= 100: return "#f59e0b"    # amber  — medium
        return                "#ef4444"    # red    — small

    colors = [bar_color(c) for c in capacities]

    fig, ax = plt.subplots(figsize=(10, max(5, len(names) * 0.8)))
    fig.patch.set_facecolor("#f8f9fa")
    ax.set_facecolor("#f8f9fa")

    # Draw horizontal bars (reversed so largest is at top)
    y_pos = np.arange(len(names))
    bars  = ax.barh(y_pos, capacities[::-1], color=colors[::-1],
                    height=0.55, edgecolor="white", linewidth=1.5)

    # Capacity labels on each bar
    for bar, cap in zip(bars, capacities[::-1]):
        ax.text(
            bar.get_width() + max(capacities) * 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"{cap} seats",
            va="center", ha="left",
            fontsize=10, fontweight="bold", color="#374151"
        )

    ax.set_yticks(y_pos)
    ax.set_yticklabels(names[::-1], fontsize=11, color="#374151")
    ax.set_xlabel("Capacity (seats)", fontsize=11, color="#6b7280", labelpad=10)
    ax.set_title("Conference Room Capacity", fontsize=16,
                 fontweight="bold", color="#1c1c1e", pad=18)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#e5e7eb")
    ax.spines["bottom"].set_color("#e5e7eb")
    ax.tick_params(colors="#9ca3af")
    ax.set_xlim(0, max(capacities) * 1.18)

    # Legend
    legend_items = [
        mpatches.Patch(color="#22c55e", label="Large (200+ seats)"),
        mpatches.Patch(color="#f59e0b", label="Medium (100–199 seats)"),
        mpatches.Patch(color="#ef4444", label="Small (<100 seats)"),
    ]
    ax.legend(handles=legend_items, loc="lower right",
              framealpha=0.8, fontsize=9)

    plt.tight_layout(pad=1.5)

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    buf.seek(0)
    plt.close(fig)

    return send_file(buf, mimetype="image/png")

# ── Run ──
if __name__ == "__main__":
    print("Conference Management API running on http://localhost:5000")
    app.run(debug=True, port=5000)

# END