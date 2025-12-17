# Quick Reference Card
## MRO Supply Scraper - All Deployment Options

---

## Choose Your Approach

### 🚀 Option 1: Hybrid Serverless (FASTEST - 2-3 hours)
**Best for:** Speed, one-time scraping, small budget
- **Duration:** 2-3 hours for 1.5M products
- **Cost:** $20-25 (mostly proxy costs)
- **Setup:** 20 minutes
- **Guide:** [HYBRID_DEPLOYMENT_GUIDE.md](HYBRID_DEPLOYMENT_GUIDE.md)

```bash
# Prerequisites: Azure account, GitHub account
# 1. Deploy Azure Functions (10 min)
# 2. Configure GitHub Secrets (5 min)
# 3. Run workflow (5 min)
# 4. Wait 2-3 hours → Download results
```

---

### 🖥️ Option 2: Azure VM (BALANCED - 18-20 hours)
**Best for:** Full control, can monitor/adjust, multiple runs
- **Duration:** 18-20 hours for 1.5M products
- **Cost:** $10-15 (VM + proxy)
- **Setup:** 20 minutes
- **Guide:** [AZURE_DEPLOYMENT_GUIDE.md](AZURE_DEPLOYMENT_GUIDE.md)

```bash
# Prerequisites: Azure account, Gmail
# 1. Create Azure VM (10 min)
# 2. Deploy scraper (5 min)
# 3. Configure .env (5 min)
# 4. Start service → Wait 18-20 hours
```

---

### 💻 Option 3: Local/VPS Server (FLEXIBLE - 15-20 days)
**Best for:** Learning, development, gradual scraping
- **Duration:** 15-20 days for 1.5M products
- **Cost:** $0 (if local) or $5-10/month VPS
- **Setup:** 30 minutes
- **Guide:** [USAGE.md](USAGE.md)

```bash
# Prerequisites: Ubuntu/Debian server
cd /home/user/Desktop/mrosupply.com
sudo bash deployment/setup.sh
sudo systemctl start mrosupply-scraper
# Wait 15-20 days → Download results
```

---

## Quick Commands by Scenario

### Scenario 1: "I want results ASAP (2-3 hours)"

**Use:** Hybrid Serverless

```bash
# 1. Deploy Azure Functions
az login
az group create --name mrosupply-scraper-rg --location eastus
az storage account create --name mrosupplystorage --resource-group mrosupply-scraper-rg --sku Standard_LRS
az functionapp create --name mrosupply-scraper-func --resource-group mrosupply-scraper-rg --storage-account mrosupplystorage --runtime python --runtime-version 3.10 --consumption-plan-location eastus

cd /home/user/Desktop/mrosupply.com/serverless/azure-functions
func azure functionapp publish mrosupply-scraper-func

# 2. Get Function URL and Key
az functionapp function show --name mrosupply-scraper-func --resource-group mrosupply-scraper-rg --function-name ScrapeBatch --query invokeUrlTemplate --output tsv
az functionapp keys list --name mrosupply-scraper-func --resource-group mrosupply-scraper-rg --query masterKey --output tsv

# 3. Add to GitHub Secrets (via web UI)
# Go to: https://github.com/YOUR_USERNAME/mrosupply-scraper/settings/secrets/actions
# Add: AZURE_FUNCTION_URL, AZURE_FUNCTION_KEY, PROXY_*, SMTP_*

# 4. Run workflow
# Go to: https://github.com/YOUR_USERNAME/mrosupply-scraper/actions
# Click "Distributed Scraping" → "Run workflow"
# Set: total_products=1500000, batch_size=100, use_azure=true, workers=50

# 5. Download results (after 2-3 hours)
# Go to completed workflow → Artifacts → Download "final-results"
```

**Total cost:** $20-25

---

### Scenario 2: "I want to run on Azure VM (18-20 hours)"

**Use:** Azure VM

```bash
# 1. Create VM via Azure Portal
# Size: Standard_D8s_v3 (8 cores, 32GB)
# OS: Ubuntu 22.04 LTS
# SSH: Enable with your public key

# 2. SSH to VM
ssh azureuser@YOUR_VM_IP

# 3. Transfer files
# On local machine:
cd /home/user/Desktop/mrosupply.com
rsync -avz --progress . azureuser@YOUR_VM_IP:/tmp/mrosupply-scraper/

# 4. Install (on VM)
cd /tmp/mrosupply-scraper
sudo bash deployment/setup.sh

# 5. Configure
sudo nano /opt/mrosupply-scraper/.env
# Set: PROXY_USER, PROXY_PASS, SMTP credentials

# 6. Start
sudo systemctl start mrosupply-scraper

# 7. Monitor
sudo systemctl status mrosupply-scraper
sudo journalctl -u mrosupply-scraper -f

# 8. Access dashboard (from local machine)
ssh -L 8080:localhost:8080 azureuser@YOUR_VM_IP
# Open: http://localhost:8080

# 9. Download results (after 18-20 hours)
scp azureuser@YOUR_VM_IP:/opt/mrosupply-scraper/data/products.json ~/Downloads/
```

**Total cost:** $10-15

---

### Scenario 3: "I want to test with 1,000 products first"

**Use:** Local machine or GitHub Actions (free)

```bash
# Option A: Local
cd /home/user/Desktop/mrosupply.com
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env
cp .env.example .env
nano .env  # Add proxy credentials

# Run
python3 scraper_rotating_residential.py \
  --target 1000 \
  --output-dir ./test_output \
  --workers 5

# Option B: GitHub Actions (free for public repos)
# Push code to GitHub
# Run workflow with:
# - total_products: 1000
# - use_azure_functions: false
# - github_workers: 10
```

**Total cost:** $0-2 (just proxy)

---

### Scenario 4: "Scraper crashed, how do I resume?"

**If using VM/Local:**
```bash
# Checkpoint file exists, just restart
sudo systemctl restart mrosupply-scraper

# Or manually:
python3 scraper_rotating_residential.py \
  --checkpoint checkpoint_products.json \
  --output-dir ./output
```

**If using Hybrid Serverless:**
```bash
# Workflow failed? Just re-run it
# Go to: GitHub Actions → Failed workflow → "Re-run failed jobs"
# It will skip already scraped batches if you modify the workflow
```

---

### Scenario 5: "How do I check progress?"

**VM/Local:**
```bash
# Service status
sudo systemctl status mrosupply-scraper

# Check checkpoint
sudo tail -20 /opt/mrosupply-scraper/data/checkpoint_products.json

# Count products
sudo jq 'length' /opt/mrosupply-scraper/data/products.json

# View logs
sudo journalctl -u mrosupply-scraper -n 50 -f

# Or open dashboard
ssh -L 8080:localhost:8080 user@server
# Open: http://localhost:8080
```

**Hybrid Serverless:**
```bash
# GitHub Actions UI
# Go to: https://github.com/YOUR_USERNAME/mrosupply-scraper/actions
# Click running workflow → View logs

# Check email
# You'll receive progress updates every 6 hours
```

---

### Scenario 6: "How do I stop the scraper?"

**VM/Local:**
```bash
# Graceful stop (saves checkpoint)
sudo systemctl stop mrosupply-scraper

# Or send SIGTERM
sudo pkill -15 -f scraper_rotating_residential

# Force stop (not recommended)
sudo systemctl kill mrosupply-scraper
```

**Hybrid Serverless:**
```bash
# Cancel workflow
# Go to: GitHub Actions → Running workflow → "Cancel workflow"

# Stop Azure Functions
az functionapp stop --name mrosupply-scraper-func --resource-group mrosupply-scraper-rg
```

---

### Scenario 7: "How do I clean up and delete everything?"

**VM/Local:**
```bash
# Stop service
sudo systemctl stop mrosupply-scraper
sudo systemctl disable mrosupply-scraper

# Delete files
sudo rm -rf /opt/mrosupply-scraper

# Remove user
sudo userdel -r scraper

# Remove systemd service
sudo rm /etc/systemd/system/mrosupply-scraper.service
sudo systemctl daemon-reload
```

**Azure (both VM and Functions):**
```bash
# Delete entire resource group (removes EVERYTHING)
az group delete --name mrosupply-scraper-rg --yes

# This deletes:
# - VM (if created)
# - Function App
# - Storage Account
# - All data

# ⚠️ DOWNLOAD RESULTS FIRST!
```

---

## Configuration Quick Reference

### .env File Template

```bash
# Proxy (Webshare)
PROXY_HOST=p.webshare.io
PROXY_PORT=10000
PROXY_USER=your_webshare_username
PROXY_PASS=your_webshare_password

# Email (Gmail)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASS=your_gmail_app_password
NOTIFICATION_EMAIL=your_email@gmail.com

# Performance
WORKERS=20              # Concurrent workers (10-50)
DELAY=0.3               # Delay between requests (0.2-1.0)
RATE_LIMIT_THRESHOLD=10 # 429 errors before cooldown
COOLDOWN_MINUTES=15     # Cooldown duration

# Resources
MEMORY_THRESHOLD_MB=3000     # Max memory before alert
DISK_SPACE_THRESHOLD_GB=5    # Min free space

# Dashboard
DASHBOARD_PORT=8080
DASHBOARD_PASSWORD=change_this_password

# Features
VALIDATE_DATA=true
ADAPTIVE_RATE=true
SMART_RETRY=true
```

---

## GitHub Secrets (for Hybrid Serverless)

Required secrets in GitHub repository settings:

| Secret Name | Value | Example |
|-------------|-------|---------|
| `AZURE_FUNCTION_URL` | Function App URL | `https://mrosupply-scraper-func.azurewebsites.net` |
| `AZURE_FUNCTION_KEY` | Function master key | `abc123...xyz789` |
| `PROXY_HOST` | Proxy hostname | `p.webshare.io` |
| `PROXY_PORT` | Proxy port | `10000` |
| `PROXY_USER` | Webshare username | `your_username` |
| `PROXY_PASS` | Webshare password | `your_password` |
| `SMTP_HOST` | Gmail SMTP | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP port | `587` |
| `SMTP_USER` | Gmail address | `your_email@gmail.com` |
| `SMTP_PASS` | Gmail app password | `your_gmail_app_password` |
| `NOTIFICATION_EMAIL` | Alert recipient | `your_email@gmail.com` |

---

## Performance Tuning

### Speed vs Reliability Trade-off

| Config | Workers | Delay | Duration | Success Rate | Cost |
|--------|---------|-------|----------|--------------|------|
| **Conservative** | 20 | 0.5s | 24h | 95%+ | $26 |
| **Balanced** | 30 | 0.3s | 18h | 90%+ | $20 |
| **Aggressive** | 50 | 0.2s | 12h | 85%+ | $18 |
| **Hybrid Serverless** | 50+ | 0.3s | 2-3h | 90%+ | $25 |

### Adjust for Rate Limiting

**If getting many 429 errors:**
```bash
# Slow down
WORKERS=15
DELAY=0.5
COOLDOWN_MINUTES=30

# Or in workflow:
github_workers: 30  # Reduce from 50
max_concurrent: 10  # Reduce Azure concurrency from 20
```

---

## Cost Breakdown

### Option 1: Hybrid Serverless
- Azure Functions: $20-25 (execution time)
- GitHub Actions: $0 (free for public repos)
- Proxy: Included in Azure cost
- **Total: $20-25**

### Option 2: Azure VM
- VM (D8s_v3): $9/day × 1 day = $9
- Storage: $1
- Bandwidth: $2
- Proxy: Included
- **Total: $12**

### Option 3: Local/VPS
- VPS (optional): $5-10/month
- Proxy: $25/month
- **Total: $25-35/month**

### Proxy Costs (All Options)
- Webshare Residential: ~$25 for 1.5M requests
- Cost per product: $0.0000167

---

## Troubleshooting Quick Fixes

### "No module named 'requests'"
```bash
pip install -r requirements.txt
```

### "Permission denied"
```bash
sudo chmod +x deployment/setup.sh
sudo chown -R scraper:scraper /opt/mrosupply-scraper
```

### "Port 8080 already in use"
```bash
# Change dashboard port
nano .env
# Set: DASHBOARD_PORT=8081
```

### "Checkpoint file corrupted"
```bash
# Use backup
cp checkpoint_products.json.backup checkpoint_products.json

# Or start fresh
rm checkpoint_products.json
```

### "Azure Function HTTP 500"
```bash
# Check logs
az functionapp log tail --name mrosupply-scraper-func --resource-group mrosupply-scraper-rg

# Restart
az functionapp restart --name mrosupply-scraper-func --resource-group mrosupply-scraper-rg
```

### "GitHub Actions failing with 'Resource not accessible'"
```bash
# Check secrets are set correctly
# Go to: Settings → Secrets → Actions
# Verify all 11 secrets exist

# Re-run workflow
# Go to: Actions → Failed workflow → "Re-run failed jobs"
```

---

## Monitoring Commands

### Check Current Progress
```bash
# VM/Local
sudo jq 'length' /opt/mrosupply-scraper/data/products.json

# Calculate percentage
python3 << 'EOF'
import json
target = 1500000
current = len(json.load(open('/opt/mrosupply-scraper/data/products.json')))
print(f"{current:,} / {target:,} ({current/target*100:.1f}%)")
EOF
```

### Check Success Rate
```bash
# From logs
sudo journalctl -u mrosupply-scraper -n 1000 | grep -E "(SUCCESS|FAILED)" | wc -l
```

### Check Disk Space
```bash
df -h /opt/mrosupply-scraper
```

### Check Memory Usage
```bash
ps aux | grep scraper_rotating_residential
```

---

## Best Practices

1. **Always test with 1,000 products first**
2. **Monitor for first hour** to ensure no issues
3. **Download results immediately** after completion
4. **Delete cloud resources** to avoid ongoing charges
5. **Keep checkpoint backups** (automated in watchdog)
6. **Use conservative settings** for first run
7. **Check email notifications** regularly
8. **Verify proxy balance** before starting

---

## Support Matrix

| Issue | VM/Local | Hybrid Serverless |
|-------|----------|-------------------|
| Pause/Resume | ✅ Yes (SIGTERM) | ❌ No (cancel & restart) |
| Real-time monitoring | ✅ Dashboard | ⚠️ Logs only |
| Auto-restart on crash | ✅ Systemd | ✅ GitHub Actions |
| Email notifications | ✅ Yes | ✅ Yes |
| Cost control | ✅ Fixed VM cost | ⚠️ Usage-based |
| Speed | ⚠️ 18-20h | ✅ 2-3h |
| Setup complexity | ⚠️ Medium | ⚠️ Medium |
| Scalability | ⚠️ Limited | ✅ Auto-scales |

---

## Decision Matrix

**Choose Hybrid Serverless if:**
- ✅ Need results fast (2-3 hours)
- ✅ One-time scraping
- ✅ Have Azure free credit
- ✅ Comfortable with serverless

**Choose Azure VM if:**
- ✅ Want full control
- ✅ Need to monitor/adjust
- ✅ Multiple scraping runs
- ✅ Prefer traditional server

**Choose Local/VPS if:**
- ✅ Learning/development
- ✅ No time pressure
- ✅ Want to understand internals
- ✅ Prefer gradual scraping

---

## Next Steps

1. **Read full guide** for your chosen approach:
   - Hybrid Serverless → [HYBRID_DEPLOYMENT_GUIDE.md](HYBRID_DEPLOYMENT_GUIDE.md)
   - Azure VM → [AZURE_DEPLOYMENT_GUIDE.md](AZURE_DEPLOYMENT_GUIDE.md)
   - Local/VPS → [USAGE.md](USAGE.md)

2. **Set up prerequisites** (proxy, email, cloud account)

3. **Test with 1,000 products** first

4. **Run full scrape** (1.5M products)

5. **Download results** and clean up

---

**Questions?** Check the troubleshooting sections in each guide.

**Ready to start?** Pick your approach above and follow the corresponding guide!
