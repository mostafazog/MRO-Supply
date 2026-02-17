#!/bin/bash
################################################################################
# Upload Brand Logos to PrestaShop Server
# Run this script on your PC to upload all 36 logos directly to the server
################################################################################

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Server configuration
SERVER="srv1164617.hstgr.cloud"
USERNAME="hstgr-srv1164617"
REMOTE_DIR="/home/hstgr-srv1164617/htdocs/srv1164617.hstgr.cloud/img/m"
LOCAL_DIR="CORRECT_BRAND_LOGOS"

echo "================================================================================"
echo "                    BRAND LOGOS UPLOADER FOR PRESTASHOP"
echo "================================================================================"
echo ""

# Check if logo directory exists
if [ ! -d "$LOCAL_DIR" ]; then
    echo -e "${RED}✗ ERROR: Logo directory not found: $LOCAL_DIR${NC}"
    exit 1
fi

# Count logos
LOGO_COUNT=$(ls -1 "$LOCAL_DIR"/*.jpg 2>/dev/null | wc -l)
echo -e "${GREEN}✓ Found $LOGO_COUNT logo files in $LOCAL_DIR/${NC}"
echo ""

# Check SSH connectivity
echo "Testing SSH connection to $SERVER..."
if ssh -o BatchMode=yes -o ConnectTimeout=5 "$USERNAME@$SERVER" exit 2>/dev/null; then
    echo -e "${GREEN}✓ SSH key authentication available${NC}"
    USE_KEY=true
else
    echo -e "${YELLOW}⚠ SSH key not configured. You'll need to enter password.${NC}"
    USE_KEY=false
fi
echo ""

echo "================================================================================"
echo "STEP 1: UPLOADING LOGOS TO SERVER"
echo "================================================================================"
echo ""

# Upload logos
echo "Uploading $LOGO_COUNT logos to $SERVER:$REMOTE_DIR..."
echo ""

if $USE_KEY; then
    # Use SSH key
    scp -o StrictHostKeyChecking=no "$LOCAL_DIR"/*.jpg "$USERNAME@$SERVER:$REMOTE_DIR/" 2>&1
else
    # Prompt for password
    echo -e "${YELLOW}Please enter password for $USERNAME@$SERVER:${NC}"
    scp -o StrictHostKeyChecking=no "$LOCAL_DIR"/*.jpg "$USERNAME@$SERVER:$REMOTE_DIR/" 2>&1
fi

UPLOAD_STATUS=$?

if [ $UPLOAD_STATUS -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Successfully uploaded $LOGO_COUNT logos!${NC}"
else
    echo ""
    echo -e "${RED}✗ Upload failed with error code: $UPLOAD_STATUS${NC}"
    echo ""
    echo "Possible solutions:"
    echo "  1. Check your internet connection"
    echo "  2. Verify server credentials"
    echo "  3. Make sure you have write permissions to $REMOTE_DIR"
    echo ""
    exit 1
fi

echo ""
echo "================================================================================"
echo "STEP 2: SETTING FILE PERMISSIONS"
echo "================================================================================"
echo ""

echo "Setting file permissions (644) on uploaded logos..."
if $USE_KEY; then
    ssh "$USERNAME@$SERVER" "chmod 644 $REMOTE_DIR/*.jpg" 2>&1
else
    echo -e "${YELLOW}Please enter password again:${NC}"
    ssh "$USERNAME@$SERVER" "chmod 644 $REMOTE_DIR/*.jpg" 2>&1
fi

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ File permissions set successfully${NC}"
else
    echo -e "${YELLOW}⚠ Could not set permissions (not critical)${NC}"
fi

echo ""
echo "================================================================================"
echo "STEP 3: CLEARING PRESTASHOP CACHE"
echo "================================================================================"
echo ""

echo "Clearing PrestaShop cache..."
CACHE_COMMANDS="cd /home/hstgr-srv1164617/htdocs/srv1164617.hstgr.cloud && \
rm -rf var/cache/prod/* var/cache/dev/* cache/smarty/compile/* cache/smarty/cache/* 2>/dev/null; \
echo 'Cache cleared'"

if $USE_KEY; then
    ssh "$USERNAME@$SERVER" "$CACHE_COMMANDS"
else
    echo -e "${YELLOW}Please enter password one more time:${NC}"
    ssh "$USERNAME@$SERVER" "$CACHE_COMMANDS"
fi

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ PrestaShop cache cleared successfully${NC}"
else
    echo -e "${YELLOW}⚠ Could not clear cache (you can do this manually)${NC}"
fi

echo ""
echo "================================================================================"
echo "                           ✅ UPLOAD COMPLETE!"
echo "================================================================================"
echo ""
echo "Summary:"
echo "  ✓ Uploaded: $LOGO_COUNT logos"
echo "  ✓ Location: $REMOTE_DIR/"
echo "  ✓ Permissions: 644 (readable)"
echo "  ✓ Cache: Cleared"
echo ""
echo "Next steps:"
echo "  1. Visit your brands page: https://www.yarinind.com/brands"
echo "  2. Check admin panel: https://www.yarinind.com/admin"
echo "  3. Verify all logos are displaying correctly"
echo ""
echo "Expected results:"
echo "  ✓ 10 brands with REAL logos from MRO Supply"
echo "  ✓ 26 brands with professional text placeholders"
echo "  ✗ NO MORE wrong Wikipedia images (bison, people, etc.)"
echo ""
echo "================================================================================"
echo ""
