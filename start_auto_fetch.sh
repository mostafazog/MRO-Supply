#!/bin/bash
# Start the auto-fetch service

# Set environment (replace YOUR_GITHUB_TOKEN_HERE with your actual token)
export GITHUB_TOKEN="${GITHUB_TOKEN:-YOUR_GITHUB_TOKEN_HERE}"
export GITHUB_REPO="mostafazog/MRO-Supply"

# Make script executable
chmod +x auto_fetch_service.py

# Start service in background
nohup python3 auto_fetch_service.py > auto_fetch_output.log 2>&1 &

# Get PID
PID=$!

echo "Auto-fetch service started with PID: $PID"
echo $PID > auto_fetch.pid

echo ""
echo "Service is now running and will check for new data every 5 minutes"
echo ""
echo "To check status:"
echo "  tail -f auto_fetch.log"
echo ""
echo "To stop service:"
echo "  kill \$(cat auto_fetch.pid)"
echo ""
echo "View consolidated data:"
echo "  ls -lh consolidated_data/"
