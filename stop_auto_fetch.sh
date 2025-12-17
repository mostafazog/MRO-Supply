#!/bin/bash
# Stop the auto-fetch service

if [ -f auto_fetch.pid ]; then
    PID=$(cat auto_fetch.pid)
    if kill -0 $PID 2>/dev/null; then
        echo "Stopping auto-fetch service (PID: $PID)..."
        kill $PID
        rm auto_fetch.pid
        echo "✓ Service stopped"
    else
        echo "Process $PID not running, removing stale PID file"
        rm auto_fetch.pid
    fi
else
    echo "No PID file found. Service may not be running."
    echo ""
    echo "Searching for running process..."
    pkill -f "auto_fetch_service.py" && echo "✓ Found and killed process" || echo "No process found"
fi
