.PHONY: dev prod install

install:
	poetry install

dev:
	poetry run python app.py

prod:
	poetry run gunicorn app:app
