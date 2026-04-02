.PHONY: install dev test format lint build-docker

install:
	pip install -r requirements.txt

dev:
	python run.py

test:
	pytest tests/ -v

format:
	ruff format .

lint:
	ruff check .

up:
	docker-compose up --build -d

down:
	docker-compose down

logs:
	docker-compose logs -f app

db-shell:
	docker exec -it retireiq_db psql -U retireiq_user -d retireiq_db
