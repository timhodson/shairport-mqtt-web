#!/usr/bin/env python3
"""
Shairport-Sync MQTT Web Interface

A Flask web application that displays now-playing information from
shairport-sync via MQTT and provides transport controls.
"""

import yaml
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
from flask import Flask, render_template, jsonify, Response

app = Flask(__name__)

# Global state for current playback
state = {
    "active": False,
    "artist": "",
    "album": "",
    "title": "",
    "genre": "",
    "volume": "",
    "client_name": "",
    "cover_art": None,  # Binary image data
    "cover_art_type": "image/jpeg",
}

# MQTT client instance
mqtt_client = None
config = None


def load_config(config_path="config.yaml"):
    """Load configuration from YAML file."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def on_connect(client, userdata, flags, reason_code, properties=None):
    """Callback when connected to MQTT broker."""
    if reason_code != 0:
        print(f"Failed to connect to MQTT broker, code: {reason_code}")
    else:
        print("Connected to MQTT broker")
        # Subscribe to all shairport topics
        base_topic = config["mqtt"]["topic"]
        client.subscribe(f"{base_topic}/#")
        print(f"Subscribed to {base_topic}/#")


def on_message(client, userdata, msg):
    """Callback when MQTT message received."""
    topic = msg.topic
    base_topic = config["mqtt"]["topic"]

    # Extract the subtopic (everything after base topic)
    if topic.startswith(base_topic + "/"):
        subtopic = topic[len(base_topic) + 1:]
    else:
        return

    # Handle different message types
    if subtopic == "artist":
        state["artist"] = msg.payload.decode("utf-8", errors="ignore")
    elif subtopic == "album":
        state["album"] = msg.payload.decode("utf-8", errors="ignore")
    elif subtopic == "title":
        state["title"] = msg.payload.decode("utf-8", errors="ignore")
    elif subtopic == "genre":
        state["genre"] = msg.payload.decode("utf-8", errors="ignore")
    elif subtopic == "volume":
        state["volume"] = msg.payload.decode("utf-8", errors="ignore")
    elif subtopic == "client_name":
        state["client_name"] = msg.payload.decode("utf-8", errors="ignore")
    elif subtopic == "cover":
        # Cover art is sent as binary data
        if msg.payload and len(msg.payload) > 0:
            state["cover_art"] = msg.payload
            # Detect image type from magic bytes
            if msg.payload[:3] == b'\xff\xd8\xff':
                state["cover_art_type"] = "image/jpeg"
            elif msg.payload[:8] == b'\x89PNG\r\n\x1a\n':
                state["cover_art_type"] = "image/png"
    elif subtopic == "active_start":
        state["active"] = True
        print("Playback session started")
    elif subtopic == "active_end":
        state["active"] = False
        # Clear metadata on session end
        state["artist"] = ""
        state["album"] = ""
        state["title"] = ""
        state["genre"] = ""
        state["cover_art"] = None
        print("Playback session ended")
    elif subtopic == "play_start":
        state["active"] = True
    elif subtopic == "play_end":
        pass  # Keep metadata visible after song ends


def on_disconnect(client, userdata, disconnect_flags, reason_code, properties=None):
    """Callback when disconnected from MQTT broker."""
    print(f"Disconnected from MQTT broker: {reason_code}")


def setup_mqtt():
    """Initialize and connect MQTT client."""
    global mqtt_client

    mqtt_config = config["mqtt"]

    # Create client (use MQTTv3.1.1 for broader compatibility)
    mqtt_client = mqtt.Client(
        callback_api_version=CallbackAPIVersion.VERSION2,
        client_id=mqtt_config.get("client_id", "shairport-web"),
        protocol=mqtt.MQTTv311
    )

    # Set callbacks
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.on_disconnect = on_disconnect

    # Set authentication if provided
    username = mqtt_config.get("username", "")
    password = mqtt_config.get("password", "")
    if username:
        mqtt_client.username_pw_set(username, password)

    # Connect to broker
    host = mqtt_config.get("host", "localhost")
    port = mqtt_config.get("port", 1883)
    print(f"Connecting to MQTT broker at {host}:{port}")
    try:
        mqtt_client.connect(host, port, keepalive=60)
        # Start MQTT loop in background thread
        mqtt_client.loop_start()
    except Exception as e:
        print(f"Failed to connect to MQTT broker: {e}")


@app.route("/")
def index():
    """Render the main web interface."""
    return render_template("index.html")


@app.route("/api/state")
def get_state():
    """Return current playback state as JSON."""
    return jsonify({
        "active": state["active"],
        "artist": state["artist"],
        "album": state["album"],
        "title": state["title"],
        "genre": state["genre"],
        "volume": state["volume"],
        "client_name": state["client_name"],
        "has_cover": state["cover_art"] is not None,
    })


@app.route("/api/cover")
def get_cover():
    """Return current cover art image."""
    if state["cover_art"]:
        return Response(
            state["cover_art"],
            mimetype=state["cover_art_type"]
        )
    else:
        # Return a placeholder or 404
        return Response(status=404)


@app.route("/api/control/<command>", methods=["POST"])
def control(command):
    """Send transport control command via MQTT.

    Supported commands:
    - play: Resume playback
    - pause: Pause playback
    - playpause: Toggle play/pause
    - next: Skip to next track (nextitem)
    - previous: Go to previous track (previtem)
    - volumeup: Increase volume
    - volumedown: Decrease volume
    - stop: Stop playback
    - shuffle: Toggle shuffle
    - repeat: Toggle repeat
    """
    if not mqtt_client:
        return jsonify({"error": "MQTT not connected"}), 503

    # Map user-friendly commands to DACP commands
    command_map = {
        "play": "play",
        "pause": "pause",
        "playpause": "playpause",
        "next": "nextitem",
        "previous": "previtem",
        "volumeup": "volumeup",
        "volumedown": "volumedown",
        "stop": "stop",
        "shuffle": "shuffle_songs",
        "repeat": "repeat",
    }

    dacp_command = command_map.get(command.lower())
    if not dacp_command:
        return jsonify({"error": f"Unknown command: {command}"}), 400

    # Publish to the remote control topic
    base_topic = config["mqtt"]["topic"]
    remote_topic = f"{base_topic}/remote"

    try:
        mqtt_client.publish(remote_topic, dacp_command)
        return jsonify({"success": True, "command": dacp_command})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def init_app():
    """Initialize the application (config and MQTT)."""
    global config
    if config is None:
        config = load_config()
        setup_mqtt()


# Initialize on module load for Gunicorn compatibility
init_app()


def main():
    """Main entry point for development server."""
    server_config = config.get("server", {})
    host = server_config.get("host", "0.0.0.0")
    port = server_config.get("port", 5000)
    debug = server_config.get("debug", False)

    print(f"Starting web server on {host}:{port}")
    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == "__main__":
    main()
