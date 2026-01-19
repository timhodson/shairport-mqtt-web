# Shairport-Sync MQTT Web Interface

A Flask web application that displays now-playing information from [shairport-sync](https://github.com/mikebrady/shairport-sync) via MQTT and provides transport controls.

![A screenshot of the web view in action](image.png)

## Features

- Real-time display of currently playing track (title, artist, album)
- Album artwork display
- Transport controls (play/pause, previous, next, volume)
- Shows active AirPlay client name
- Clean, responsive web interface

## Prerequisites

- Python 3.9+
- [Poetry](https://python-poetry.org/) for dependency management
- shairport-sync configured with MQTT metadata output
- An MQTT broker (e.g., Mosquitto)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/shairport-mqtt-web.git
   cd shairport-mqtt-web
   ```

2. Install dependencies:
   ```bash
   make install
   ```

3. Copy the example config and edit with your settings:
   ```bash
   cp config.yaml.example config.yaml
   ```

4. Edit `config.yaml` with your MQTT broker details:
   ```yaml
   mqtt:
     host: "your-mqtt-broker"
     port: 1883
     username: ""  # if required
     password: ""  # if required
     topic: "shairport"  # must match shairport-sync config
   ```

## Usage

### Development

```bash
make dev
```

### Production

```bash
make prod
```

The web interface will be available at `http://localhost:5001` (or the port configured in `config.yaml`).

### Linux Service Installation

To install as a systemd service on Linux (e.g., Raspberry Pi):

1. First, ensure you have configured `config.yaml` with your settings.

2. Deploy and install the service:
   ```bash
   make deploy
   ```

   This will:
   - Copy files to `/opt/shairport-mqtt-web`
   - Create a Python virtual environment
   - Install the systemd service
   - Enable the service to start on boot

3. Start the service:
   ```bash
   sudo systemctl start shairport-mqtt-web
   ```

4. Check status:
   ```bash
   sudo systemctl status shairport-mqtt-web
   ```

5. View logs:
   ```bash
   sudo journalctl -u shairport-mqtt-web -f
   ```

To update and redeploy after making changes:
```bash
make redeploy
```

To uninstall the service:
```bash
make uninstall-service
```

**Note:** The service uses systemd's `DynamicUser` feature which creates a temporary user automatically.

## shairport-sync Configuration

Ensure your shairport-sync is configured to publish metadata via MQTT. Add the following to your shairport-sync configuration:

```
mqtt = {
    enabled = "yes";
    hostname = "your-mqtt-broker";
    port = 1883;
    topic = "shairport";
    publish_cover = "yes";
    enable_remote = "yes";  // for transport controls
};
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main web interface |
| `/api/state` | GET | Current playback state as JSON |
| `/api/cover` | GET | Current album artwork |
| `/api/control/<command>` | POST | Send transport control |

### Available Commands

- `play` - Resume playback
- `pause` - Pause playback
- `playpause` - Toggle play/pause
- `next` - Skip to next track
- `previous` - Go to previous track
- `volumeup` - Increase volume
- `volumedown` - Decrease volume

## License

MIT
