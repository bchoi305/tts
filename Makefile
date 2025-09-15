.PHONY: dev worker up down fmt

dev:
	python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

worker:
	OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES PATH="/opt/homebrew/bin:$(PATH)" python start_simple_worker.py

up:
	docker-compose up -d --build

down:
	docker-compose down -v

