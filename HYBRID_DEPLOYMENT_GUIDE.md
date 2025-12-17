# Hybrid Serverless Deployment Guide
## GitHub Actions + Azure Functions for 24-Hour Scraping

**Target:** Scrape 1.5M products in 2-3 hours using distributed serverless architecture

**Cost:** ~$20-25 total (GitHub Actions free + Azure Functions execution)

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Part 1: Deploy Azure Functions](#part-1-deploy-azure-functions)
4. [Part 2: Configure GitHub Repository](#part-2-configure-github-repository)
5. [Part 3: Run the Workflow](#part-3-run-the-workflow)
6. [Part 4: Monitor Progress](#part-4-monitor-progress)
7. [Part 5: Download Results](#part-5-download-results)
8. [Troubleshooting](#troubleshooting)
9. [Cost Optimization](#cost-optimization)

---

## Overview

### Architecture

```
┌──────────────────────────────────────────────────────────┐
│                   GitHub Actions                          │
│                                                           │
│  ┌─────────────┐    ┌──────────────────────────┐        │
│  │  Prepare    │───▶│  Matrix: 50 Workers      │        │
│  │  Batches    │    │  (Parallel Scraping)     │        │
│  └─────────────┘    └──────────────────────────┘        │
│         │                                                 │
│         │ Send remaining batches                         │
│         ▼                                                 │
│  ┌─────────────────────────────────────────────┐        │
│  │  Orchestrate Azure Functions                │        │
│  │  (Send 14,950 batches to Azure)             │        │
│  └─────────────────────────────────────────────┘        │
│         │                                                 │
└─────────┼─────────────────────────────────────────────────┘
          │ HTTP POST
          ▼
┌──────────────────────────────────────────────────────────┐
│                   Azure Functions                         │
│                                                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ Function │  │ Function │  │ Function │  │   ...   │ │
│  │    1     │  │    2     │  │    3     │  │         │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
│                                                           │
│              Auto-scales to 100+ instances                │
│              Each scrapes 100 products                    │
└──────────────────────────────────────────────────────────┘
```

### Performance Estimates

- **GitHub Actions:** 50 batches × 100 products = 5,000 products
- **Azure Functions:** 14,950 batches × 100 products = 1,495,000 products
- **Total Duration:** 2-3 hours
- **Total Cost:** $20-25 (Azure Functions execution + bandwidth)

---

## Prerequisites

### 1. Azure Account

- **Option 1:** New Azure account with $200 free credit
  - Go to https://azure.microsoft.com/free/
  - Sign up with credit card (won't be charged)
  - Get $200 credit valid for 30 days

- **Option 2:** Existing Azure account with pay-as-you-go

### 2. GitHub Account

- Free account is sufficient
- Public repository = unlimited Actions minutes
- Private repository = 2,000 free minutes/month

### 3. Gmail Account (for notifications)

- **Already configured:** your_email@gmail.com
- **App password:** your_gmail_app_password

### 4. Webshare Proxy Account

- **Service:** https://www.webshare.io/
- **Plan needed:** Rotating Residential Proxies
- **Cost:** ~$25 for 1.5M requests
- **Credentials:** Your PROXY_USER and PROXY_PASS

### 5. Required Tools

```bash
# Install Azure Functions Core Tools
# For Ubuntu/Debian:
curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg
sudo mv microsoft.gpg /etc/apt/trusted.gpg.d/microsoft.gpg
sudo sh -c 'echo "deb [arch=amd64] https://packages.microsoft.com/repos/microsoft-ubuntu-$(lsb_release -cs)-prod $(lsb_release -cs) main" > /etc/apt/sources.list.d/dotnetdev.list'
sudo apt-get update
sudo apt-get install azure-functions-core-tools-4

# Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Verify installation
func --version  # Should show 4.x
az --version    # Should show Azure CLI version
```

---

## Part 1: Deploy Azure Functions

### Step 1.1: Login to Azure

```bash
# Login to Azure
az login

# Set subscription (if you have multiple)
az account list --output table
az account set --subscription "Your Subscription Name"

# Verify
az account show
```

### Step 1.2: Create Resource Group

```bash
# Create resource group in East US region
az group create \
  --name mrosupply-scraper-rg \
  --location eastus

# Verify
az group show --name mrosupply-scraper-rg
```

### Step 1.3: Create Storage Account

```bash
# Create storage account (required for Azure Functions)
az storage account create \
  --name mrosupplystorage \
  --resource-group mrosupply-scraper-rg \
  --location eastus \
  --sku Standard_LRS \
  --kind StorageV2

# Get connection string (save this!)
az storage account show-connection-string \
  --name mrosupplystorage \
  --resource-group mrosupply-scraper-rg \
  --query connectionString \
  --output tsv
```

**⚠️ SAVE THE CONNECTION STRING** - You'll need it later!

### Step 1.4: Create Function App

```bash
# Create Function App (Consumption Plan = Auto-scaling)
az functionapp create \
  --name mrosupply-scraper-func \
  --resource-group mrosupply-scraper-rg \
  --storage-account mrosupplystorage \
  --runtime python \
  --runtime-version 3.10 \
  --functions-version 4 \
  --consumption-plan-location eastus \
  --os-type Linux

# Verify
az functionapp show \
  --name mrosupply-scraper-func \
  --resource-group mrosupply-scraper-rg
```

### Step 1.5: Configure Function App Settings

```bash
# Set proxy configuration
az functionapp config appsettings set \
  --name mrosupply-scraper-func \
  --resource-group mrosupply-scraper-rg \
  --settings \
    "PROXY_HOST=p.webshare.io" \
    "PROXY_PORT=10000" \
    "PROXY_USER=your_webshare_username" \
    "PROXY_PASS=your_webshare_password"

# ⚠️ IMPORTANT: Replace your_webshare_username and your_webshare_password with actual credentials!
```

### Step 1.6: Deploy Function Code

```bash
# Navigate to Azure Functions directory
cd /home/user/Desktop/mrosupply.com/serverless/azure-functions

# Deploy to Azure
func azure functionapp publish mrosupply-scraper-func --python

# Wait for deployment (2-3 minutes)
# You should see:
# ✅ Deployment successful
# ✅ Remote build succeeded!
```

### Step 1.7: Get Function URL and Key

```bash
# Get function URL
az functionapp function show \
  --name mrosupply-scraper-func \
  --resource-group mrosupply-scraper-rg \
  --function-name ScrapeBatch \
  --query invokeUrlTemplate \
  --output tsv

# Get function key (master key)
az functionapp keys list \
  --name mrosupply-scraper-func \
  --resource-group mrosupply-scraper-rg \
  --query masterKey \
  --output tsv
```

**⚠️ SAVE THESE VALUES:**
- **Function URL:** `https://mrosupply-scraper-func.azurewebsites.net`
- **Function Key:** (long alphanumeric string)

### Step 1.8: Test Function

```bash
# Test with curl
curl -X POST "https://mrosupply-scraper-func.azurewebsites.net/api/scrape?code=YOUR_FUNCTION_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://www.mrosupply.com/product/0000001",
      "https://www.mrosupply.com/product/0000002"
    ],
    "batch_id": 0
  }'

# Expected response:
# {
#   "batch_id": 0,
#   "total": 2,
#   "success": 2,
#   "failed": 0,
#   "products": [...],
#   "timestamp": 1234567890
# }
```

✅ **If you see the response above, your Azure Function is working!**

---

## Part 2: Configure GitHub Repository

### Step 2.1: Create GitHub Repository

**Option A: Use existing repository**
- If you already have the code in a GitHub repo, skip to Step 2.2

**Option B: Create new repository**

```bash
cd /home/user/Desktop/mrosupply.com

# Initialize git (if not already)
git init

# Create .gitignore
cat > .gitignore << 'EOF'
.env
*.log
__pycache__/
*.pyc
venv/
.vscode/
checkpoint_products.json
data/
output/
EOF

# Add all files
git add .
git commit -m "Initial commit: MRO Supply scraper with hybrid serverless"

# Create repository on GitHub
# Go to: https://github.com/new
# Name: mrosupply-scraper
# Public or Private (public = unlimited Actions minutes)
# Click "Create repository"

# Push to GitHub
git remote add origin https://github.com/YOUR_USERNAME/mrosupply-scraper.git
git branch -M main
git push -u origin main
```

### Step 2.2: Configure GitHub Secrets

GitHub Secrets are encrypted environment variables used in workflows.

**Navigate to:**
1. Go to your repository: `https://github.com/YOUR_USERNAME/mrosupply-scraper`
2. Click **Settings** tab
3. Click **Secrets and variables** → **Actions**
4. Click **New repository secret**

**Add the following secrets:**

#### Secret 1: AZURE_FUNCTION_URL
- **Name:** `AZURE_FUNCTION_URL`
- **Value:** `https://mrosupply-scraper-func.azurewebsites.net`
- Click **Add secret**

#### Secret 2: AZURE_FUNCTION_KEY
- **Name:** `AZURE_FUNCTION_KEY`
- **Value:** (paste the function key from Step 1.7)
- Click **Add secret**

#### Secret 3: PROXY_HOST
- **Name:** `PROXY_HOST`
- **Value:** `p.webshare.io`
- Click **Add secret**

#### Secret 4: PROXY_PORT
- **Name:** `PROXY_PORT`
- **Value:** `10000`
- Click **Add secret**

#### Secret 5: PROXY_USER
- **Name:** `PROXY_USER`
- **Value:** (your Webshare username)
- Click **Add secret**

#### Secret 6: PROXY_PASS
- **Name:** `PROXY_PASS`
- **Value:** (your Webshare password)
- Click **Add secret**

#### Secret 7: SMTP_HOST
- **Name:** `SMTP_HOST`
- **Value:** `smtp.gmail.com`
- Click **Add secret**

#### Secret 8: SMTP_PORT
- **Name:** `SMTP_PORT`
- **Value:** `587`
- Click **Add secret**

#### Secret 9: SMTP_USER
- **Name:** `SMTP_USER`
- **Value:** `your_email@gmail.com`
- Click **Add secret**

#### Secret 10: SMTP_PASS
- **Name:** `SMTP_PASS`
- **Value:** `your_gmail_app_password`
- Click **Add secret**

#### Secret 11: NOTIFICATION_EMAIL
- **Name:** `NOTIFICATION_EMAIL`
- **Value:** `your_email@gmail.com` (or where you want notifications)
- Click **Add secret**

**Verify all secrets are added:**
You should see 11 secrets listed:
- AZURE_FUNCTION_URL
- AZURE_FUNCTION_KEY
- PROXY_HOST
- PROXY_PORT
- PROXY_USER
- PROXY_PASS
- SMTP_HOST
- SMTP_PORT
- SMTP_USER
- SMTP_PASS
- NOTIFICATION_EMAIL

---

## Part 3: Run the Workflow

### Step 3.1: Navigate to Actions Tab

1. Go to your repository on GitHub
2. Click **Actions** tab
3. You should see: **"Distributed Scraping - GitHub Actions + Azure Functions"**

### Step 3.2: Start the Workflow

1. Click on the workflow name: **"Distributed Scraping - GitHub Actions + Azure Functions"**
2. Click **Run workflow** button (on the right)
3. Configure parameters:

**Workflow Inputs:**

| Parameter | Default | Recommended | Description |
|-----------|---------|-------------|-------------|
| `total_products` | 1500000 | 1500000 | Total products to scrape |
| `batch_size` | 100 | 100 | Products per batch (don't change) |
| `use_azure_functions` | true | true | Use Azure Functions for scaling |
| `github_workers` | 50 | 50 | GitHub Actions parallel workers |

**For 1.5M products (recommended):**
- total_products: `1500000`
- batch_size: `100`
- use_azure_functions: `true`
- github_workers: `50`

**For testing (5,000 products):**
- total_products: `5000`
- batch_size: `100`
- use_azure_functions: `false`
- github_workers: `50`

4. Click **Run workflow** (green button)

### Step 3.3: Workflow Starts

You'll see the workflow run appear with status: **🟡 In progress**

**Jobs that will run:**

1. **prepare** (1 minute)
   - Calculates total batches needed
   - Splits work between GitHub Actions and Azure Functions
   - Creates batch assignments

2. **scrape-github** (30 minutes)
   - 50 parallel workers
   - Each scrapes 100 products
   - Total: 5,000 products

3. **orchestrate-azure** (2-3 hours)
   - Sends 14,950 batches to Azure Functions
   - Azure auto-scales to handle load
   - Total: 1,495,000 products

4. **aggregate** (5 minutes)
   - Combines results from GitHub + Azure
   - Generates summary statistics

5. **notify** (1 minute)
   - Sends completion email to your_email@gmail.com

**Total Duration:** 2-3 hours

---

## Part 4: Monitor Progress

### Option 1: GitHub Actions UI (Recommended)

1. Go to **Actions** tab in your repository
2. Click on the running workflow
3. You'll see all jobs with status indicators:
   - ✅ Green checkmark = Completed
   - 🟡 Yellow circle = Running
   - ❌ Red X = Failed

**Click on each job to see logs:**
- **prepare** → Shows batch distribution
- **scrape-github** → Click on individual matrix jobs (Batch 0, Batch 1, etc.)
- **orchestrate-azure** → Shows Azure Functions progress
- **aggregate** → Shows final statistics

### Option 2: Real-Time Logs

**Watch specific job:**
1. Click on job name (e.g., "Orchestrate Azure Functions")
2. Click on step name (e.g., "Send batches to Azure Functions")
3. Logs update in real-time

**Example log output:**
```
Sending 14,950 batches to Azure Functions
Starting from batch 50

✓ Batch 50: 98/100 success
✓ Batch 51: 100/100 success
✓ Batch 52: 99/100 success
...
Progress: 100/14950 batches (100 success, 0 failed)
Progress: 200/14950 batches (198 success, 2 failed)
...
✅ Azure Functions completed:
   Success: 14,900 batches
   Failed: 50 batches
   Total: 14,950 batches
```

### Option 3: Azure Portal

1. Go to https://portal.azure.com
2. Navigate to your Function App: **mrosupply-scraper-func**
3. Click **Monitor** → **Logs**
4. You'll see:
   - Number of function invocations
   - Success/failure rate
   - Response times
   - Error messages (if any)

### Option 4: Email Notifications

You'll receive emails at: **your_email@gmail.com**

**Email 1: Startup (within 1 minute)**
```
Subject: 🚀 Distributed Scraping Started

Distributed Scraping Job Started

GitHub Actions: 50 workers
Azure Functions: 14,950 batches
Total: 1,500,000 products

Workflow: https://github.com/YOUR_USERNAME/mrosupply-scraper/actions/runs/...
```

**Email 2: Progress (every 6 hours, configurable)**
```
Subject: 📊 Scraping Progress Update

Progress: 500,000 / 1,500,000 (33%)
Success rate: 95%
Estimated completion: 1.5 hours
```

**Email 3: Completion (when done)**
```
Subject: ✅ Distributed Scraping Completed

Distributed Scraping Job Completed

GitHub Actions: 5,000 products
Azure Functions: 14,900 batches

Total estimated: 1,495,000 products

Workflow: https://github.com/YOUR_USERNAME/mrosupply-scraper/actions/runs/...

Download artifacts to get full results.
```

---

## Part 5: Download Results

### Step 5.1: Navigate to Completed Workflow

1. Go to **Actions** tab
2. Click on completed workflow run (should have ✅ green checkmark)
3. Scroll down to **Artifacts** section

### Step 5.2: Download Artifacts

You'll see several artifacts:

**1. github-batch-0 through github-batch-49**
- Results from GitHub Actions workers
- Each contains:
  - `batch_X_products.json` - Scraped products
  - `batch_X_failed.json` - Failed URLs

**2. azure-summary**
- Summary of Azure Functions execution
- Contains: `azure_summary.json`
- Shows success/failed batch counts

**3. final-results** (Most Important)
- Contains:
  - `final_summary.json` - Complete statistics
  - `SCRAPING_REPORT.md` - Human-readable report

**Download all artifacts:**
- Click **Download all artifacts** (zip file, ~3-4 GB)

**Or download specific artifact:**
- Click on artifact name (e.g., "final-results")
- Download button appears

### Step 5.3: Extract and Review

```bash
# Extract downloaded zip
cd ~/Downloads
unzip mrosupply-scraper-artifacts.zip

# Navigate to final results
cd final-results

# View summary
cat final_summary.json

# Example output:
# {
#   "github_products": 5000,
#   "github_errors": 125,
#   "azure_success_batches": 14900,
#   "azure_failed_batches": 50,
#   "total_batches": 15000
# }

# View report
cat SCRAPING_REPORT.md
```

### Step 5.4: Combine All Products

```bash
# Navigate to artifacts directory
cd ~/Downloads/mrosupply-scraper-artifacts

# Combine all GitHub products
python3 << 'EOF'
import json
from pathlib import Path

all_products = []

# Load products from GitHub batches
for batch_dir in Path('.').glob('github-batch-*'):
    for json_file in batch_dir.glob('batch_*_products.json'):
        with open(json_file) as f:
            products = json.load(f)
            all_products.extend(products)

print(f"Total GitHub products: {len(all_products):,}")

# Save combined file
with open('all_github_products.json', 'w') as f:
    json.dump(all_products, f, indent=2)

print(f"✅ Saved to: all_github_products.json")
EOF
```

**Note:** Azure Functions results are returned to the orchestrator but not saved individually as artifacts to reduce storage. If you need full Azure results, modify the workflow to upload them to Azure Blob Storage.

---

## Troubleshooting

### Issue 1: Azure Function Deployment Failed

**Error:** `Deployment failed with status code: 500`

**Solution:**
```bash
# Check Function App logs
az functionapp log tail \
  --name mrosupply-scraper-func \
  --resource-group mrosupply-scraper-rg

# Redeploy
cd /home/user/Desktop/mrosupply.com/serverless/azure-functions
func azure functionapp publish mrosupply-scraper-func --python --build remote
```

### Issue 2: GitHub Actions Workflow Not Appearing

**Problem:** Actions tab shows "Get started with GitHub Actions"

**Solution:**
1. Ensure workflow file is in correct location: `.github/workflows/distributed-scrape-azure.yml`
2. Check file syntax:
   ```bash
   cd /home/user/Desktop/mrosupply.com
   cat .github/workflows/distributed-scrape-azure.yml | head -10
   ```
3. Commit and push:
   ```bash
   git add .github/workflows/distributed-scrape-azure.yml
   git commit -m "Add distributed scraping workflow"
   git push
   ```

### Issue 3: Azure Function Returns HTTP 500

**Error in logs:** `HTTP 500 for batch X`

**Debugging:**
```bash
# Check Azure Function logs
az monitor log-analytics query \
  --workspace YOUR_WORKSPACE_ID \
  --analytics-query "traces | where message contains 'error' | take 20"

# Common causes:
# 1. Proxy credentials incorrect
# 2. Memory limit exceeded
# 3. Timeout (>10 minutes)

# Fix proxy credentials:
az functionapp config appsettings set \
  --name mrosupply-scraper-func \
  --resource-group mrosupply-scraper-rg \
  --settings \
    "PROXY_USER=correct_username" \
    "PROXY_PASS=correct_password"
```

### Issue 4: Rate Limiting (HTTP 429)

**Symptoms:** Many batches fail with "Rate limit exceeded"

**Solution:**
1. **Increase delays in workflow:**
   ```yaml
   # Edit .github/workflows/distributed-scrape-azure.yml
   # Line ~232: Change max_concurrent
   max_concurrent = 10  # Reduce from 20 to 10
   ```

2. **Adjust batch size:**
   - Run workflow with smaller `batch_size` (50 instead of 100)

3. **Slow down GitHub workers:**
   ```yaml
   # Line ~129: Increase WORKERS setting
   WORKERS=2  # Reduce from 3 to 2
   ```

### Issue 5: No Email Notifications Received

**Check:**
1. **Gmail App Password correct?**
   - Test with:
   ```bash
   python3 << 'EOF'
   import smtplib
   from email.mime.text import MIMEText

   msg = MIMEText("Test")
   msg['Subject'] = 'Test'
   msg['From'] = 'your_email@gmail.com'
   msg['To'] = 'your_email@gmail.com'

   with smtplib.SMTP('smtp.gmail.com', 587) as server:
       server.starttls()
       server.login('your_email@gmail.com', 'your_gmail_app_password')
       server.send_message(msg)
   print("✅ Email sent successfully")
   EOF
   ```

2. **Check spam folder**

3. **Verify secrets are set correctly** in GitHub Settings → Secrets

### Issue 6: Workflow Stuck on "Orchestrate Azure Functions"

**Problem:** Job runs for hours with no progress

**Solution:**
1. **Check Azure Function App is running:**
   ```bash
   az functionapp show \
     --name mrosupply-scraper-func \
     --resource-group mrosupply-scraper-rg \
     --query state
   # Should show: "Running"
   ```

2. **Check Azure Functions quota:**
   - Free tier: 1,000,000 executions/month
   - Consumption plan: Unlimited (pay per execution)

3. **Manually test Azure Function:**
   ```bash
   curl -X POST "https://mrosupply-scraper-func.azurewebsites.net/api/scrape?code=YOUR_KEY" \
     -H "Content-Type: application/json" \
     -d '{"urls": ["https://www.mrosupply.com/product/0000001"], "batch_id": 999}'
   ```

### Issue 7: High Azure Costs

**Check current costs:**
1. Go to https://portal.azure.com
2. Navigate to **Cost Management + Billing**
3. Click **Cost analysis**
4. View spending by service

**Expected costs for 1.5M products:**
- Azure Functions executions: 15,000 × $0.0000002 = $0.003
- Azure Functions execution time: 15,000 × 30s × $0.000016/GB-s = ~$20-25
- Storage: < $1
- **Total: $20-26**

**If costs higher:**
- Check for failed batches causing retries
- Verify auto-scaling isn't over-provisioning
- Set spending limit in Azure portal

---

## Cost Optimization

### 1. Use Free Tiers

- **GitHub Actions:** Unlimited minutes for public repositories
- **Azure Free Credit:** $200 for new accounts (covers everything)

### 2. Optimize Batch Distribution

**For 1.5M products:**
- GitHub Actions: 5,000 products (free)
- Azure Functions: 1,495,000 products (~$25)

**To save costs, increase GitHub workers:**
```yaml
# In workflow inputs:
github_workers: 200  # Instead of 50

# This gives:
# - GitHub Actions: 20,000 products (free)
# - Azure Functions: 1,480,000 products (~$24)
```

**Note:** GitHub has max 256 parallel jobs, so max `github_workers: 256`

### 3. Clean Up Resources After Completion

```bash
# Delete Resource Group (removes everything)
az group delete \
  --name mrosupply-scraper-rg \
  --yes \
  --no-wait

# This deletes:
# - Function App
# - Storage Account
# - All data

# ⚠️ IMPORTANT: Download results BEFORE deleting!
```

### 4. Use Spot Instances (Advanced)

For very large scraping jobs, consider Azure Container Instances with Spot pricing (70% discount).

---

## Performance Tuning

### 1. Adjust Concurrency

**GitHub Actions workers:**
```yaml
# .github/workflows/distributed-scrape-azure.yml
# Line ~20-21
github_workers:
  default: '50'  # Try: 100, 150, 200, 256

# Line ~100
max-parallel: 50  # Match github_workers value
```

**Azure Functions concurrency:**
```bash
# Increase concurrent requests
az functionapp config set \
  --name mrosupply-scraper-func \
  --resource-group mrosupply-scraper-rg \
  --prewarmed-instance-count 10
```

### 2. Optimize Batch Size

**Current:** 100 products/batch = 15,000 batches

**Larger batches (faster, but less fault-tolerant):**
- Batch size: 500 → 3,000 batches
- Each batch takes 5-10 minutes
- Fewer Azure Function invocations = lower cost

**Smaller batches (slower, but more resilient):**
- Batch size: 50 → 30,000 batches
- Each batch takes 1-2 minutes
- Better fault tolerance (less data lost per failure)

**Recommendation:** Keep at 100 (good balance)

### 3. Regional Optimization

Deploy Azure Functions in region closest to:
- Target website (mrosupply.com) → US East
- Proxy servers (Webshare) → US East

**Current deployment:** `eastus` (optimal)

---

## Advanced: Queue-Based Architecture

For even better scalability, use Azure Storage Queues:

### Architecture

```
GitHub Actions → Enqueue URLs → Azure Queue
                                     ↓
                          Azure Functions (Queue Trigger)
                                     ↓
                          Process → Results Queue
                                     ↓
                          Aggregator Function
```

### Benefits

- **Better fault tolerance:** Failed messages auto-retry
- **Better scaling:** Azure auto-scales based on queue depth
- **Better monitoring:** Built-in metrics for queue length

### Implementation

Already included in `function_app.py`:
- `ScrapeFromQueue` function (queue-triggered)
- `AggregateBatchResults` function (blob-triggered)

**To use:**
1. Create Azure Storage Queue: `scrape-queue`
2. Modify workflow to enqueue URLs instead of HTTP POST
3. Monitor queue depth in Azure Portal

---

## Summary: Quick Reference

### Deploy Azure Functions
```bash
az login
az group create --name mrosupply-scraper-rg --location eastus
az storage account create --name mrosupplystorage --resource-group mrosupply-scraper-rg --sku Standard_LRS
az functionapp create --name mrosupply-scraper-func --resource-group mrosupply-scraper-rg --storage-account mrosupplystorage --runtime python --runtime-version 3.10 --consumption-plan-location eastus
cd /home/user/Desktop/mrosupply.com/serverless/azure-functions
func azure functionapp publish mrosupply-scraper-func
```

### Configure GitHub Secrets
1. Go to repository Settings → Secrets → Actions
2. Add 11 secrets (AZURE_FUNCTION_URL, AZURE_FUNCTION_KEY, proxies, SMTP)

### Run Workflow
1. Go to Actions tab
2. Select "Distributed Scraping - GitHub Actions + Azure Functions"
3. Click "Run workflow"
4. Set parameters (1500000 products, 100 batch size, true for Azure, 50 workers)
5. Click "Run workflow"

### Monitor Progress
- GitHub Actions UI (real-time logs)
- Email notifications (startup, completion)
- Azure Portal (function invocations)

### Download Results
1. Go to completed workflow run
2. Scroll to Artifacts
3. Download "final-results"
4. Extract and review `final_summary.json`

### Clean Up
```bash
# Download results first!
az group delete --name mrosupply-scraper-rg --yes
```

---

## Estimated Timeline

| Phase | Duration | Status |
|-------|----------|--------|
| Deploy Azure Functions | 10 minutes | ⏳ |
| Configure GitHub | 5 minutes | ⏳ |
| Run workflow (prepare) | 1 minute | ⏳ |
| GitHub Actions scraping | 30 minutes | ⏳ |
| Azure Functions scraping | 2-3 hours | ⏳ |
| Aggregation | 5 minutes | ⏳ |
| **Total** | **~3 hours** | ⏳ |

---

## Support

**Issues?** Check:
1. [Troubleshooting](#troubleshooting) section above
2. GitHub Actions logs
3. Azure Function App logs
4. Email notifications for errors

**Cost concerns?**
- Expected: $20-25
- Check Azure Cost Management
- Delete resources when done

**Questions about the workflow?**
- Review workflow file: `.github/workflows/distributed-scrape-azure.yml`
- Check README files in `serverless/` directory

---

**Ready to start?** Go to [Part 1: Deploy Azure Functions](#part-1-deploy-azure-functions)

**Testing first?** Use these settings when running workflow:
- total_products: `5000`
- use_azure_functions: `false`
- github_workers: `50`

This will scrape only 5,000 products using GitHub Actions (free, ~10 minutes).
