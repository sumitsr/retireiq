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

build-docker:
	docker build -t retireiq-backend .

run-docker:
	docker run -p 5000:5000 --env-file .env retireiq-backend
