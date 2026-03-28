import json
import os

from flask import Flask, jsonify, render_template, send_file

app = Flask(__name__)

ROOM_NAME = "room7"
ROOM_DIR = os.path.join(app.root_path, "content", "rooms", ROOM_NAME)


def load_scene():
    path = os.path.join(ROOM_DIR, f"{ROOM_NAME}.json")
    with open(path) as f:
        data = json.load(f)

    data["room"] = ROOM_NAME

    for name in ("video.mp4", "video.webm"):
        if os.path.exists(os.path.join(ROOM_DIR, name)):
            data["video"] = f"/content/rooms/{ROOM_NAME}/{name}"
            break

    for name in ("panorama.jpg", "panorama.png", "panorama.jpeg", "panorama.webp"):
        if os.path.exists(os.path.join(ROOM_DIR, name)):
            data["image"] = f"/content/rooms/{ROOM_NAME}/{name}"
            break

    for name in ("music.mp3", "music.ogg", "music.wav"):
        if os.path.exists(os.path.join(ROOM_DIR, name)):
            data["audio"] = f"/content/rooms/{ROOM_NAME}/{name}"
            break

    hotspots_dir = os.path.join(ROOM_DIR, "hotspots")
    for hs in data.get("hotspots", []):
        hs_json = os.path.join(hotspots_dir, hs["id"], "hotspot.json")
        if os.path.exists(hs_json):
            with open(hs_json) as f:
                hs_data = json.load(f)
            hs.setdefault("desc", hs_data.get("desc"))
            if "popup" in hs_data:
                hs.setdefault("popup", hs_data["popup"])

    return data


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/content/<path:subpath>")
def content_file(subpath):
    return send_file(os.path.join(app.root_path, "content", subpath))


@app.route("/api/scene")
def api_scene():
    return jsonify(load_scene())


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5000)
