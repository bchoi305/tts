.PHONY: dev worker up down fmt

dev:
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

worker:
	python -c "from redis import Redis; from rq import Worker, Queue; from app.config import settings; r=Redis.from_url(settings.redis_url); Worker([Queue(settings.queue_name, connection=r)], connection=r).work()"

up:
	docker-compose up -d --build

down:
	docker-compose down -v

