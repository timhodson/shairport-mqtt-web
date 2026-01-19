import yaml

# Load config from config.yaml
with open("config.yaml") as f:
    _cfg = yaml.safe_load(f)

_server = _cfg.get("server", {})
bind = f"{_server.get('host', '0.0.0.0')}:{_server.get('port', 5000)}"
workers = 1  # Single worker to share MQTT state
