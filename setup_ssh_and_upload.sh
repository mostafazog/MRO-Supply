#!/bin/bash
################################################################################
# Setup SSH Access and Upload Brand Logos
# This script will:
# 1. Add your SSH key to the server (requires password once)
# 2. Upload all 36 brand logos
# 3. Clear PrestaShop cache
################################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;36m'
NC='\033[0m'

SERVER="srv1164617.hstgr.cloud"
USERNAME="hstgr-srv1164617"
REMOTE_DIR="/home/hstgr-srv1164617/htdocs/srv1164617.hstgr.cloud/img/m"
LOCAL_DIR="CORRECT_BRAND_LOGOS"
PUBLIC_KEY="$HOME/.ssh/id_rsa.pub"

echo "================================================================================"
echo "           BRAND LOGOS UPLOADER WITH SSH KEY SETUP"
echo "================================================================================"
echo ""

# Check if logos exist
if [ ! -d "$LOCAL_DIR" ]; then
    echo -e "${RED}✗ ERROR: Logo directory not found: $LOCAL_DIR${NC}"
    exit 1
fi

LOGO_COUNT=$(ls -1 "$LOCAL_DIR"/*.jpg 2>/dev/null | wc -l)
echo -e "${GREEN}✓ Found $LOGO_COUNT logo files ready to upload${NC}"
echo ""

# Check if SSH key exists
if [ ! -f "$PUBLIC_KEY" ]; then
    echo -e "${RED}✗ ERROR: SSH public key not found: $PUBLIC_KEY${NC}"
    exit 1
fi

echo -e "${BLUE}Your SSH public key:${NC}"
echo "$(cat $PUBLIC_KEY)"
echo ""

# Test if SSH key is already authorized
echo "Testing SSH connection..."
if ssh -o BatchMode=yes -o ConnectTimeout=5 "$USERNAME@$SERVER" exit 2>/dev/null; then
    echo -e "${GREEN}✓ SSH key already authorized!${NC}"
    NEED_SETUP=false
else
    echo -e "${YELLOW}⚠ SSH key not authorized yet${NC}"
    NEED_SETUP=true
fi
echo ""

# Setup SSH key if needed
if [ "$NEED_SETUP" = true ]; then
    echo "================================================================================"
    echo "STEP 1: SETTING UP SSH KEY (You'll need to enter password ONCE)"
    echo "================================================================================"
    echo ""
    echo "This will authorize your SSH key on the server so you won't need"
    echo "to enter passwords again in the future."
    echo ""
    echo -e "${YELLOW}Please enter your server password when prompted:${NC}"
    echo ""

    # Use ssh-copy-id to add key
    if command -v ssh-copy-id &> /dev/null; then
        ssh-copy-id -i "$PUBLIC_KEY" "$USERNAME@$SERVER"
    else
        # Manual method if ssh-copy-id is not available
        cat "$PUBLIC_KEY" | ssh "$USERNAME@$SERVER" "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && echo 'SSH key added successfully'"
    fi

    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✓ SSH key setup complete!${NC}"
        echo ""
    else
        echo ""
        echo -e "${RED}✗ SSH key setup failed${NC}"
        echo ""
        echo "Alternative: You can add the key manually via cPanel:"
        echo "1. Login to cPanel"
        echo "2. Go to 'SSH Access' → 'Manage SSH Keys'"
        echo "3. Import this public key:"
        echo "$(cat $PUBLIC_KEY)"
        echo ""
        exit 1
    fi
fi

echo "================================================================================"
echo "STEP 2: UPLOADING BRAND LOGOS"
echo "================================================================================"
echo ""
echo "Uploading $LOGO_COUNT logos to $SERVER..."
echo ""

# Upload logos using SCP
scp -o StrictHostKeyChecking=no "$LOCAL_DIR"/*.jpg "$USERNAME@$SERVER:$REMOTE_DIR/"

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Successfully uploaded $LOGO_COUNT logos!${NC}"
else
    echo ""
    echo -e "${RED}✗ Upload failed${NC}"
    exit 1
fi

echo ""
echo "================================================================================"
echo "STEP 3: SETTING FILE PERMISSIONS"
echo "================================================================================"
echo ""

ssh "$USERNAME@$SERVER" "chmod 644 $REMOTE_DIR/*.jpg && echo '✓ Permissions set to 644'"

echo ""
echo "================================================================================"
echo "STEP 4: CLEARING PRESTASHOP CACHE"
echo "================================================================================"
echo ""

CACHE_CMD="cd /home/hstgr-srv1164617/htdocs/srv1164617.hstgr.cloud && \
rm -rf var/cache/prod/* var/cache/dev/* cache/smarty/compile/* cache/smarty/cache/* 2>/dev/null && \
echo 'PrestaShop cache cleared'"

ssh "$USERNAME@$SERVER" "$CACHE_CMD"

echo ""
echo "================================================================================"
echo "                        ✅ UPLOAD COMPLETE!"
echo "================================================================================"
echo ""
echo -e "${GREEN}Summary:${NC}"
echo "  ✓ Uploaded: $LOGO_COUNT brand logos"
echo "  ✓ Location: $REMOTE_DIR/"
echo "  ✓ Permissions: 644"
echo "  ✓ Cache: Cleared"
echo ""
echo -e "${BLUE}What was uploaded:${NC}"
echo "  ✓ 10 REAL logos from MRO Supply (Alemite, Bando, Mitutoyo, etc.)"
echo "  ✓ 26 Professional text placeholders"
echo "  ✗ NO MORE wrong Wikipedia images!"
echo ""
echo -e "${GREEN}Next Steps:${NC}"
echo "  1. Visit: https://www.yarinind.com/brands"
echo "  2. Check admin: https://www.yarinind.com/admin → Catalog → Brands"
echo "  3. Verify all logos are displaying correctly"
echo ""
echo "================================================================================"
echo ""
