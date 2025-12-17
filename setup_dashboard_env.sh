#!/bin/bash
# Setup environment variables for enhanced dashboard

echo "==================================================================="
echo "Setting up Enhanced Dashboard Environment"
echo "==================================================================="
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    touch .env
fi

# Add GitHub token (get from GitHub settings > Developer settings > Personal access tokens)
read -p "Enter GitHub Personal Access Token: " GITHUB_TOKEN
echo "export GITHUB_TOKEN='$GITHUB_TOKEN'" >> .env
echo "export GITHUB_REPO='mostafazog/MRO-Supply'" >> .env

# Add Azure Function settings
echo "export AZURE_FUNCTION_URL='https://mrosupply-scraper-func.azurewebsites.net'" >> .env
read -p "Enter Azure Function Key: " AZURE_KEY
echo "export AZURE_FUNCTION_KEY='$AZURE_KEY'" >> .env

# Add Webshare settings
read -p "Enter Webshare API Key: " WEBSHARE_KEY
echo "export WEBSHARE_API_KEY='$WEBSHARE_KEY'" >> .env
echo "export PROXY_HOST='p.webshare.io'" >> .env
echo "export PROXY_PORT='10000'" >> .env
read -p "Enter Proxy Username: " PROXY_USER
read -p "Enter Proxy Password: " PROXY_PASS
echo "export PROXY_USER='$PROXY_USER'" >> .env
echo "export PROXY_PASS='$PROXY_PASS'" >> .env

echo ""
echo "✅ Environment variables configured!"
echo ""
echo "To use the dashboard:"
echo "  1. Load environment: source .env"
echo "  2. Run dashboard: python3 enhanced_dashboard.py"
echo ""
echo "Dashboard features:"
echo "  - Local scraper control"
echo "  - GitHub Actions monitoring"
echo "  - Azure Functions monitoring"
echo "  - Real-time status updates"
echo ""
echo "==================================================================="
