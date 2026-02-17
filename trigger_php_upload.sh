#!/bin/bash
################################################################################
# Trigger PHP Upload Script on Server
# This will call the PHP uploader directly via HTTP
################################################################################

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "================================================================================"
echo "           TRIGGERING PHP LOGO UPLOADER ON SERVER"
echo "================================================================================"
echo ""

# Check if upload_via_php.php exists in GitHub
echo "Checking if upload script is available..."

UPLOAD_URL="https://raw.githubusercontent.com/mostafazog/MRO-Supply/main/upload_via_php.php"

if curl --output /dev/null --silent --head --fail "$UPLOAD_URL"; then
    echo -e "${GREEN}✓ Upload script found on GitHub${NC}"
else
    echo -e "${RED}✗ Upload script not found${NC}"
    exit 1
fi

echo ""
echo "This will:"
echo "  1. Download the PHP uploader to server (via curl/wget)"
echo "  2. Execute it to install all 36 logos"
echo "  3. Clean up after completion"
echo ""

# Create a command to download and run the PHP script
CMD="cd /home/hstgr-srv1164617/htdocs/srv1164617.hstgr.cloud && \
wget -q https://raw.githubusercontent.com/mostafazog/MRO-Supply/main/upload_via_php.php -O upload_logos_temp.php && \
php upload_logos_temp.php && \
rm -f upload_logos_temp.php"

echo -e "${YELLOW}Attempting SSH connection to run uploader...${NC}"
echo ""

# Try to run via SSH
if ssh -o BatchMode=yes -o ConnectTimeout=10 hstgr-srv1164617@srv1164617.hstgr.cloud "$CMD" 2>/dev/null; then
    echo ""
    echo -e "${GREEN}✓ Upload completed successfully via SSH!${NC}"
else
    echo -e "${YELLOW}⚠ SSH key not configured${NC}"
    echo ""
    echo "MANUAL METHOD:"
    echo "=============="
    echo ""
    echo "Please run these commands on your server (via cPanel Terminal or SSH):"
    echo ""
    echo "cd /home/hstgr-srv1164617/htdocs/srv1164617.hstgr.cloud"
    echo "wget https://raw.githubusercontent.com/mostafazog/MRO-Supply/main/upload_via_php.php -O upload_logos.php"
    echo "php upload_logos.php"
    echo "rm upload_logos.php"
    echo ""
    echo "Or visit this URL in your browser:"
    echo "https://www.yarinind.com/upload_via_php.php"
    echo "(After uploading upload_via_php.php to server root)"
    echo ""
fi

echo "================================================================================"
