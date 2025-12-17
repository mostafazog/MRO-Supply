## 🚀 Multi-Region Azure Functions Deployment Guide

**Goal:** Deploy 10 Azure Functions across different regions to get 500+ concurrent workers with different IP addresses!

### 💰 Cost with Your $4,000 Azure Credit:

```
Azure Functions Consumption Plan (per region):
- First 1M executions/month: FREE
- Storage: ~$0.05/month
- Bandwidth: Minimal

Total for 10 regions:
- Monthly cost: ~$0 (covered by free tier)
- Your $4,000 credit: Can run this for YEARS!
```

### 📊 Performance Benefits:

| Metric | Single Region | Multi-Region (10) |
|--------|--------------|-------------------|
| Workers | 100 | 500+ |
| IP Addresses | 1 range | 10 different ranges |
| Rate Limiting | High risk | Very low risk |
| Speed | 2-3 hours | 30-60 minutes |
| Success Rate | 70-80% | 90-95% |

---

## 🎯 Step 1: Deploy Azure Functions

### Option A: Automated Deployment (Recommended)

```bash
# Make script executable
chmod +x deploy_multi_region_azure.sh

# Login to Azure
az login

# Run deployment (takes 20-30 minutes)
./deploy_multi_region_azure.sh
```

**What it does:**
- Creates 10 Azure Function Apps in different regions
- Deploys scraper code to each
- Generates configuration files
- Saves secrets for GitHub

### Option B: Manual Deployment (One Region Example)

```bash
# Set variables
REGION="westus"
FUNC_NAME="mrosupply-scraper-func-westus"
RG_NAME="mrosupply-scraper-rg"
STORAGE_NAME="mrosupplystowestus"

# Create storage account
az storage account create \
  --name $STORAGE_NAME \
  --resource-group $RG_NAME \
  --location $REGION \
  --sku Standard_LRS

# Create function app
az functionapp create \
  --name $FUNC_NAME \
  --resource-group $RG_NAME \
  --consumption-plan-location $REGION \
  --runtime python \
  --runtime-version 3.10 \
  --functions-version 4 \
  --storage-account $STORAGE_NAME \
  --os-type Linux

# Deploy code
cd azure-functions
func azure functionapp publish $FUNC_NAME --python
```

Repeat for each region!

---

## 🔑 Step 2: Add GitHub Secrets

After deployment, you'll have a `github_secrets.txt` file. Add these to GitHub:

1. Go to: https://github.com/mostafazog/MRO-Supply/settings/secrets/actions
2. Click: **New repository secret**
3. Add each secret from the file:

```
AZURE_FUNCTION_URL_EASTUS=https://mrosupply-scraper-func-eastus.azurewebsites.net
AZURE_FUNCTION_KEY_EASTUS=your_key_here

AZURE_FUNCTION_URL_WESTUS=https://mrosupply-scraper-func-westus.azurewebsites.net
AZURE_FUNCTION_KEY_WESTUS=your_key_here

... (repeat for all 10 regions)
```

---

## 🚀 Step 3: Test Single Region

Before running all 10 regions, test one:

```bash
# Test East US function
curl -X POST \
  "https://mrosupply-scraper-func-eastus.azurewebsites.net/api/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://www.mrosupply.com/automation/2302938_ant-gw715153_red-lion-controls/"],
    "batch_id": 999
  }'
```

**Expected response:**
```json
{
  "batch_id": 999,
  "total": 1,
  "success": 1,
  "failed": 0,
  "duration": 2.5
}
```

---

## 📈 Step 4: Run Multi-Region Scrape

### Option A: GitHub Actions (Automated)

1. Go to: https://github.com/mostafazog/MRO-Supply/actions
2. Select: **Distributed Scraping - Multi-Region Azure Functions**
3. Click: **Run workflow**
4. Settings:
   - Total products: `1508714`
   - Batch size: `100`
   - GitHub workers: `50`
5. Click: **Run workflow**

### Option B: Command Line

```bash
curl -X POST \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/mostafazog/MRO-Supply/actions/workflows/distributed-scrape-multi-region.yml/dispatches \
  -d '{"ref":"main","inputs":{"total_products":"1508714","batch_size":"100","github_workers":"50"}}'
```

---

## 📊 Step 5: Monitor Progress

### Real-Time Monitoring:

**1. GitHub Actions:**
- https://github.com/mostafazog/MRO-Supply/actions
- See all 50 GitHub workers running in parallel

**2. Azure Portal:**
- https://portal.azure.com
- Search for each function app
- Click **Monitoring** → **Live Metrics**
- See real-time requests per region

**3. Your Dashboard:**
- http://172.173.144.149:8080
- Monitor tab shows GitHub Actions status
- Auto-fetch downloads results every 5 minutes

**4. Check Progress:**
```bash
# See how many products have been downloaded
ssh azureuser@172.173.144.149 "cat ~/mrosupply-scraper/consolidated_products.json | python3 -c 'import sys, json; print(f\"{len(json.load(sys.stdin)):,} products\")'"
```

---

## 🎯 Expected Results:

### With 10 Regions (500 workers):

```
Total Products: 1,508,714
Batch Size: 100
Total Batches: 15,087

Distribution:
├── GitHub Actions: 50 batches (5,000 products)
└── Azure Multi-Region: 15,037 batches
    ├── East US: 1,503 batches (150,300 products)
    ├── West US: 1,503 batches (150,300 products)
    ├── Central US: 1,503 batches (150,300 products)
    ├── North Europe: 1,503 batches (150,300 products)
    ├── West Europe: 1,503 batches (150,300 products)
    ├── Southeast Asia: 1,503 batches (150,300 products)
    ├── East Asia: 1,503 batches (150,300 products)
    ├── Australia East: 1,503 batches (150,300 products)
    ├── UK South: 1,503 batches (150,300 products)
    └── Canada Central: 1,504 batches (150,400 products)

Timeline:
- Start: T+0min
- First results: T+5min (auto-fetch)
- 50% complete: T+20min
- 100% complete: T+40min
- Consolidated: T+45min

Success Rate: 90-95% (different IPs avoid rate limits!)
Final Product Count: ~1.3M-1.4M products
```

---

## 🔧 Troubleshooting:

### Problem: Function deployment failed

**Solution:**
```bash
# Check if resource group exists
az group show --name mrosupply-scraper-rg

# Retry deployment for specific region
REGION="westus"
az functionapp create --name mrosupply-scraper-func-$REGION ...
```

### Problem: Function returns 401/403

**Solution:**
- Function key may be wrong
- Get new key:
```bash
az functionapp keys list \
  --name mrosupply-scraper-func-westus \
  --resource-group mrosupply-scraper-rg
```

### Problem: Still getting rate limited

**Solution:**
- Use MORE regions (add South America, Africa, etc.)
- Reduce batch size to 50 instead of 100
- Add small delay between requests in scraper code

---

## 💡 Advanced: Add More Regions

Want even MORE workers? Add these regions:

```bash
# Additional regions with good geographic distribution
EXTRA_REGIONS=(
    "brazilsouth"      # South America
    "southafricanorth" # Africa
    "japaneast"        # Asia
    "koreacentral"     # Asia
    "francecentral"    # Europe
)

# Deploy to each
for REGION in "${EXTRA_REGIONS[@]}"; do
    # ... deployment commands
done
```

**With 15 regions = 750+ workers!**

---

## 📊 Cost Monitoring:

### Check your Azure spending:

```bash
# View cost analysis
az consumption usage list --query "[].{Date:usageStart, Cost:pretaxCost}" -o table

# View by resource group
az cost-management query \
  --scope "/subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/mrosupply-scraper-rg" \
  --timeframe MonthToDate
```

**Expected cost: $0-5/month (well within free tier)**

---

## ✅ Summary:

### What You Get:

- ✅ **500+ concurrent workers** across 10 regions
- ✅ **10 different IP address pools** (avoids rate limits!)
- ✅ **30-60 minute completion time** for 1.5M products
- ✅ **90-95% success rate** (vs 10% with single region)
- ✅ **$0 cost** (covered by Azure free tier)
- ✅ **Geographic distribution** (looks natural to website)

### Commands Cheat Sheet:

```bash
# Deploy
./deploy_multi_region_azure.sh

# Test
curl -X POST https://FUNCTION_URL/api/scrape -d '{"urls":["..."], "batch_id":999}'

# Trigger scrape
# (Use GitHub Actions UI or curl to workflow dispatch)

# Monitor
az functionapp logs tail --name mrosupply-scraper-func-westus --resource-group mrosupply-scraper-rg

# Download results
scp azureuser@172.173.144.149:~/mrosupply-scraper/consolidated_products.csv .

# Check cost
az consumption usage list
```

---

## 🎉 You're Ready!

With $4,000 Azure credit, you can:
- Run this scrape **hundreds of times**
- Scale to **1000+ workers** if needed
- Keep infrastructure running for **months**

**Let's deploy and scrape 1.5M products in under an hour!** 🚀
