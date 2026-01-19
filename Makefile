.PHONY: dev prod install deploy install-service uninstall-service redeploy

INSTALL_DIR = /opt/shairport-mqtt-web
SERVICE_FILE = shairport-mqtt-web.service

install:
	poetry install

dev:
	poetry run python app.py

prod:
	poetry run gunicorn app:app

deploy: install-service
	@echo "Deployment complete. Start with: sudo systemctl start shairport-mqtt-web"

install-service:
	@echo "Installing to $(INSTALL_DIR)..."
	sudo mkdir -p $(INSTALL_DIR)
	sudo cp -r app.py config.yaml gunicorn.conf.py templates static pyproject.toml poetry.lock $(INSTALL_DIR)/
	sudo cp config.yaml.example $(INSTALL_DIR)/ 2>/dev/null || true
	cd $(INSTALL_DIR) && sudo python3 -m venv .venv && sudo $(INSTALL_DIR)/.venv/bin/pip install poetry && sudo $(INSTALL_DIR)/.venv/bin/poetry install --only main
	@echo "Installing systemd service..."
	sudo cp $(SERVICE_FILE) /etc/systemd/system/
	sudo systemctl daemon-reload
	sudo systemctl enable shairport-mqtt-web
	@echo "Service installed and enabled."

uninstall-service:
	@echo "Stopping and disabling service..."
	-sudo systemctl stop shairport-mqtt-web
	-sudo systemctl disable shairport-mqtt-web
	sudo rm -f /etc/systemd/system/$(SERVICE_FILE)
	sudo systemctl daemon-reload
	@echo "Removing installation directory..."
	sudo rm -rf $(INSTALL_DIR)
	@echo "Uninstalled."

redeploy:
	@echo "Pulling latest code..."
	git pull
	@echo "Stopping service..."
	-sudo systemctl stop shairport-mqtt-web
	@echo "Updating files..."
	sudo cp -r app.py gunicorn.conf.py templates static pyproject.toml poetry.lock $(INSTALL_DIR)/
	sudo cp $(SERVICE_FILE) /etc/systemd/system/
	@echo "Installing dependencies..."
	cd $(INSTALL_DIR) && sudo $(INSTALL_DIR)/.venv/bin/poetry install --only main
	@echo "Reloading and starting service..."
	sudo systemctl daemon-reload
	sudo systemctl start shairport-mqtt-web
	@echo "Redeploy complete."
