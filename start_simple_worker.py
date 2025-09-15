#!/usr/bin/env python3

import os
import signal
from redis import Redis
from rq import SimpleWorker, Queue

# macOS compatibility
os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES'
os.environ['PATH'] = '/opt/homebrew/bin:' + os.environ.get('PATH', '')

# Lightweight .env loader (no external dependency)
ENV_PATH = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(ENV_PATH):
    with open(ENV_PATH, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, val = line.split('=', 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                # Do not overwrite if already set in the environment
                if key and (key not in os.environ):
                    os.environ[key] = val

from app.config import settings


def signal_handler(signum, frame):
    print(f"\n[Worker] Received signal {signum}. Shutting down gracefully...")
    raise SystemExit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == '__main__':
    print("[Worker] Starting SimpleWorker (no forking) ...")
    redis_conn = Redis.from_url(settings.redis_url)
    queue = Queue(settings.queue_name, connection=redis_conn)

    worker = SimpleWorker([queue], connection=redis_conn)

    print(f"[Worker] Listening on queue: {settings.queue_name}")
    print(f"[Worker] Redis URL: {settings.redis_url}")
    print("[Worker] Press Ctrl+C to stop.")

    worker.work()
