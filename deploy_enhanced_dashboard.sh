#!/bin/bash
# Deploy Enhanced Dashboard to Server

SERVER_IP="172.173.144.149"
SERVER_USER="azureuser"

echo "=========================================================================="
echo "🚀 DEPLOYING ENHANCED DASHBOARD TO SERVER"
echo "=========================================================================="
echo ""
echo "Server: $SERVER_USER@$SERVER_IP"
echo ""

# Upload enhanced dashboard
echo "📤 Step 1: Uploading enhanced dashboard files..."
scp enhanced_dashboard.py $SERVER_USER@$SERVER_IP:~/mrosupply-scraper/
scp templates/enhanced_dashboard.html $SERVER_USER@$SERVER_IP:~/mrosupply-scraper/templates/ 2>/dev/null || echo "  (Template already exists)"

echo ""
echo "📤 Step 2: Uploading configuration..."

# Create environment setup script on server
ssh $SERVER_USER@$SERVER_IP << 'ENDSSH'
cd ~/mrosupply-scraper

# Create .env file with credentials
cat > .env << 'EOF'
# GitHub (for workflow monitoring)
export GITHUB_TOKEN='YOUR_GITHUB_TOKEN_HERE'
export GITHUB_REPO='mostafazog/MRO-Supply'

# Azure Functions
export AZURE_FUNCTION_URL='https://mrosupply-scraper-func.azurewebsites.net'
export AZURE_FUNCTION_KEY='YOUR_AZURE_FUNCTION_KEY_HERE'

# Webshare Proxy
export WEBSHARE_API_KEY='hqy10ekhqb0jackvwe9fyzf4aosmo28wi6s48zji'
export PROXY_HOST='p.webshare.io'
export PROXY_PORT='10000'
export PROXY_USER='yopfgyku'
export PROXY_PASS='pn4xri0h48sy'

# Dashboard settings
export DASHBOARD_PASSWORD='admin123'
export DASHBOARD_PORT='8080'
export DASHBOARD_HOST='0.0.0.0'
export OUTPUT_DIR='full_scrape'
EOF

echo "✅ Environment configured"
ENDSSH

echo ""
echo "🔄 Step 3: Restarting dashboard..."

ssh $SERVER_USER@$SERVER_IP << 'ENDSSH'
cd ~/mrosupply-scraper

# Kill old dashboard
pkill -f "python3.*enhanced_dashboard" 2>/dev/null || pkill -f "python3.*dashboard" 2>/dev/null
sleep 2

# Start new enhanced dashboard
echo "Starting enhanced dashboard..."
source .env
nohup python3 enhanced_dashboard.py > dashboard.log 2>&1 &

sleep 3

# Check if running
if pgrep -f "enhanced_dashboard" > /dev/null; then
    echo "✅ Enhanced dashboard started successfully!"
    echo ""
    echo "Dashboard is now running with:"
    echo "  - GitHub Actions monitoring"
    echo "  - Azure Functions monitoring"
    echo "  - Local scraper control"
else
    echo "❌ Failed to start dashboard"
    echo "Check logs: tail -f ~/mrosupply-scraper/dashboard.log"
fi
ENDSSH

echo ""
echo "=========================================================================="
echo "✅ DEPLOYMENT COMPLETE"
echo "=========================================================================="
echo ""
echo "Enhanced Dashboard URL: http://$SERVER_IP:8080"
echo "Password: admin123"
echo ""
echo "New Features:"
echo "  ✅ Monitor GitHub Actions workflows"
echo "  ✅ Monitor Azure Functions status"
echo "  ✅ View all 3 systems in one dashboard"
echo "  ✅ Real-time distributed scraping progress"
echo ""
echo "=========================================================================="
