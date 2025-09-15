#!/bin/bash

echo "=== TTS Worker Status ==="
# Count both classic Worker and SimpleWorker
WORKER_COUNT=$(ps aux | egrep "(Worker.*Queue|start_simple_worker\.py)" | grep -v grep | wc -l | xargs)
echo "Worker Count: $WORKER_COUNT"

if [ "$WORKER_COUNT" -eq 0 ]; then
    echo "❌ No workers running"
elif [ "$WORKER_COUNT" -eq 1 ]; then
    echo "✅ Single worker running (optimal)"
    ps aux | egrep "(Worker.*Queue|start_simple_worker\.py)" | grep -v grep | awk '{print "  PID: "$2", Started: "$9}'
else
    echo "⚠️  Multiple workers detected ($WORKER_COUNT) - May cause conflicts!"
    ps aux | egrep "(Worker.*Queue|start_simple_worker\.py)" | grep -v grep | awk '{print "  PID: "$2", Started: "$9}'
fi
echo "=========================="