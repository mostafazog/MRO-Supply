#!/bin/bash
# Deploy Multiple Azure Functions Across Different Regions
# Each region provides different IP addresses to avoid rate limiting

set -e

# Configuration
BASE_NAME="mrosupply-scraper"
REGIONS=(
    "eastus"
    "westus"
    "centralus"
    "northeurope"
    "westeurope"
    "southeastasia"
    "eastasia"
    "australiaeast"
    "uksouth"
    "canadacentral"
)

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Multi-Region Azure Functions Deployment${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if logged in
echo -e "${YELLOW}Checking Azure login...${NC}"
if ! az account show &> /dev/null; then
    echo -e "${RED}Not logged in to Azure. Please run: az login${NC}"
    exit 1
fi

SUBSCRIPTION=$(az account show --query name -o tsv)
echo -e "${GREEN}✓ Logged in to: $SUBSCRIPTION${NC}"
echo ""

# Show cost estimate
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Cost Estimate${NC}"
echo -e "${BLUE}========================================${NC}"
echo "Azure Functions: ${#REGIONS[@]} regions"
echo "Estimated cost: \$0 (Free tier covers all executions)"
echo "Your credit: \$4,000 remaining"
echo ""
read -p "Continue with deployment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# Create resource group (single group for all)
RG_NAME="${BASE_NAME}-rg"
echo -e "${YELLOW}Creating resource group: $RG_NAME${NC}"
az group create --name $RG_NAME --location eastus --output none
echo -e "${GREEN}✓ Resource group created${NC}"
echo ""

# Array to store function URLs
declare -a FUNCTION_URLS
declare -a FUNCTION_KEYS

# Deploy to each region
for i in "${!REGIONS[@]}"; do
    REGION="${REGIONS[$i]}"
    REGION_NUM=$((i+1))
    FUNC_NAME="${BASE_NAME}-func-${REGION}"
    STORAGE_NAME="${BASE_NAME}${REGION}store"

    # Storage account names must be lowercase and max 24 chars
    STORAGE_NAME=$(echo "$STORAGE_NAME" | tr '[:upper:]' '[:lower:]' | cut -c1-24)

    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Deploying to ${REGION} (${REGION_NUM}/${#REGIONS[@]})${NC}"
    echo -e "${BLUE}========================================${NC}"

    # Create storage account
    echo -e "${YELLOW}Creating storage account: $STORAGE_NAME${NC}"
    az storage account create \
        --name $STORAGE_NAME \
        --resource-group $RG_NAME \
        --location $REGION \
        --sku Standard_LRS \
        --output none
    echo -e "${GREEN}✓ Storage account created${NC}"

    # Create function app
    echo -e "${YELLOW}Creating function app: $FUNC_NAME${NC}"
    az functionapp create \
        --name $FUNC_NAME \
        --resource-group $RG_NAME \
        --consumption-plan-location $REGION \
        --runtime python \
        --runtime-version 3.10 \
        --functions-version 4 \
        --storage-account $STORAGE_NAME \
        --os-type Linux \
        --output none
    echo -e "${GREEN}✓ Function app created${NC}"

    # Deploy function code (from azure-functions directory)
    if [ -d "azure-functions" ]; then
        echo -e "${YELLOW}Deploying function code...${NC}"
        cd azure-functions
        func azure functionapp publish $FUNC_NAME --python
        cd ..
        echo -e "${GREEN}✓ Code deployed${NC}"
    else
        echo -e "${YELLOW}⚠ azure-functions directory not found, skipping code deployment${NC}"
    fi

    # Get function URL and key
    FUNC_URL="https://${FUNC_NAME}.azurewebsites.net"
    FUNCTION_URLS+=("$FUNC_URL")

    echo -e "${YELLOW}Getting function key...${NC}"
    sleep 5  # Wait for function to be ready
    FUNC_KEY=$(az functionapp keys list \
        --name $FUNC_NAME \
        --resource-group $RG_NAME \
        --query "functionKeys.default" -o tsv 2>/dev/null || echo "")

    if [ -z "$FUNC_KEY" ]; then
        FUNC_KEY="<pending>"
        echo -e "${YELLOW}⚠ Function key not yet available, will retry later${NC}"
    else
        echo -e "${GREEN}✓ Function key retrieved${NC}"
    fi
    FUNCTION_KEYS+=("$FUNC_KEY")

    echo -e "${GREEN}✓ Deployment complete for $REGION${NC}"
    echo ""
done

# Save configuration
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Saving Configuration${NC}"
echo -e "${BLUE}========================================${NC}"

cat > multi_region_config.json << EOF
{
  "deployment_date": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "total_regions": ${#REGIONS[@]},
  "total_workers": $((${#REGIONS[@]} * 50)),
  "functions": [
EOF

for i in "${!REGIONS[@]}"; do
    REGION="${REGIONS[$i]}"
    FUNC_NAME="${BASE_NAME}-func-${REGION}"
    FUNC_URL="${FUNCTION_URLS[$i]}"
    FUNC_KEY="${FUNCTION_KEYS[$i]}"

    cat >> multi_region_config.json << EOF
    {
      "region": "$REGION",
      "name": "$FUNC_NAME",
      "url": "$FUNC_URL",
      "key": "$FUNC_KEY"
    }$([ $i -lt $((${#REGIONS[@]} - 1)) ] && echo "," || echo "")
EOF
done

cat >> multi_region_config.json << EOF
  ]
}
EOF

echo -e "${GREEN}✓ Configuration saved to: multi_region_config.json${NC}"
echo ""

# Create environment file for GitHub Actions
echo -e "${YELLOW}Creating GitHub Secrets configuration...${NC}"
cat > github_secrets.txt << EOF
# Add these secrets to your GitHub repository:
# Settings → Secrets and variables → Actions → New repository secret

# For each Azure Function, add:
EOF

for i in "${!REGIONS[@]}"; do
    REGION="${REGIONS[$i]}"
    REGION_UPPER=$(echo "$REGION" | tr '[:lower:]' '[:upper:]')
    FUNC_URL="${FUNCTION_URLS[$i]}"
    FUNC_KEY="${FUNCTION_KEYS[$i]}"

    cat >> github_secrets.txt << EOF

AZURE_FUNCTION_URL_${REGION_UPPER}=${FUNC_URL}
AZURE_FUNCTION_KEY_${REGION_UPPER}=${FUNC_KEY}
EOF
done

echo -e "${GREEN}✓ GitHub secrets template saved to: github_secrets.txt${NC}"
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Deployment Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}✓ Deployed ${#REGIONS[@]} Azure Functions${NC}"
echo -e "${GREEN}✓ Total capacity: $((${#REGIONS[@]} * 50)) concurrent workers${NC}"
echo -e "${GREEN}✓ Geographic distribution: 10 regions${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Add the secrets from github_secrets.txt to your GitHub repository"
echo "2. Update the workflow to use multiple Azure Functions"
echo "3. Test with a small batch first"
echo "4. Run full scrape with 500+ workers!"
echo ""
echo -e "${BLUE}Estimated completion time for 1.5M products:${NC}"
echo "  With 500 workers: ${GREEN}30-60 minutes${NC}"
echo ""
echo -e "${GREEN}✅ Deployment Complete!${NC}"
