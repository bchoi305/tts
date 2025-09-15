#!/usr/bin/env python3

import os
import signal
from redis import Redis
from rq import Worker, Queue

# Set macOS compatibility
os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES'
os.environ['PATH'] = '/opt/homebrew/bin:' + os.environ.get('PATH', '')

# Import settings after environment is set
from app.config import settings

def signal_handler(signum, frame):
    print(f"\nReceived signal {signum}. Shutting down gracefully...")
    exit(0)

# Set up signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == '__main__':
    print("Starting single RQ worker (no fork)...")
    
    # Connect to Redis
    redis_conn = Redis.from_url(settings.redis_url)
    
    # Create queue
    queue = Queue(settings.queue_name, connection=redis_conn)
    
    # Create worker with no forking
    worker = Worker([queue], connection=redis_conn)
    
    print(f"Worker listening on queue: {settings.queue_name}")
    print(f"Redis URL: {settings.redis_url}")
    print("Press Ctrl+C to stop...")
    
    # Start worker (this blocks)
    worker.work()