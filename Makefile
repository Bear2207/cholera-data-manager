.PHONY: up down logs clean install test

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

clean:
	docker compose down -v

install:
	pip install -r requirements.txt

test:
	python -m pytest tests/

load:
	python scripts/run_pipeline.py

check:
	python scripts/check_data.py