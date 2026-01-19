import yaml

# Load config from config.yaml
with open("config.yaml") as f:
    _cfg = yaml.safe_load(f)

_server = _cfg.get("server", {})
bind = f"{_server.get('host', '0.0.0.0')}:{_server.get('port', 5000)}"
workers = 1  # Single worker to share MQTT state
threads = 4  # Multiple threads for handling SSE connections
timeout = 0  # Disable timeout for long-lived SSE connections
keepalive = 65  # Keep connections alive
