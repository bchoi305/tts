#!/bin/bash

# Function to check if workers are running
check_workers() {
    ps aux | grep "Worker.*Queue" | grep -v grep | wc -l | xargs
}

# Kill any existing workers with force
echo "Checking for existing workers..."
WORKER_COUNT=$(check_workers)
if [ "$WORKER_COUNT" -gt 0 ]; then
    echo "Found $WORKER_COUNT workers. Killing them..."
    pkill -9 -f "Worker.*Queue" 2>/dev/null
    sleep 2
    
    # Double check
    REMAINING=$(check_workers)
    if [ "$REMAINING" -gt 0 ]; then
        echo "Warning: $REMAINING workers still running"
        ps aux | grep "Worker.*Queue" | grep -v grep | awk '{print "  PID: "$2}' | xargs kill -9 2>/dev/null
        sleep 1
    fi
fi

echo "All workers cleared. Starting single worker..."

# Set environment for macOS
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
export PATH="/opt/homebrew/bin:$PATH"

# Start single worker with explicit process replacement
exec python -c "from redis import Redis; from rq import Worker, Queue; from app.config import settings; r=Redis.from_url(settings.redis_url); Worker([Queue(settings.queue_name, connection=r)], connection=r).work()"
