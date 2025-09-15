#!/bin/bash

# Set environment variables for macOS compatibility
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
export PATH="/opt/homebrew/bin:$PATH"

# Use the correct Python environment
PYTHON_PATH="/Users/my_studio/.local/share/mamba/envs/ai38/bin/python"

# Start the worker
$PYTHON_PATH -c "from redis import Redis; from rq import Worker, Queue; from app.config import settings; r=Redis.from_url(settings.redis_url); Worker([Queue(settings.queue_name, connection=r)], connection=r).work()"