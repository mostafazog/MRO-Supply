# MRO Supply Scraping System - Complete Overview

## System Status: FULLY AUTOMATED ✅

Everything is now connected and running automatically!

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     COMPLETE SCRAPING SYSTEM                    │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│  GitHub Actions  │      │ Azure Functions  │      │  Auto-Fetch      │
│  50 Workers      │      │ 100+ Workers     │      │  Service         │
│  Dynamic IPs     │      │ Dynamic IPs      │      │  (Background)    │
└────────┬─────────┘      └────────┬─────────┘      └────────┬─────────┘
         │                         │                         │
         │ Scrapes                 │ Scrapes                 │ Downloads
         │ Products                │ Products                │ Artifacts
         │                         │                         │
         ▼                         ▼                         ▼
    ┌────────────────────────────────────────────────────────────┐
    │              GitHub Actions Artifacts                      │
    │              (Temporary Storage)                           │
    └──────────────────────────┬─────────────────────────────────┘
                               │
                               │ Every 5 minutes
                               ▼
                    ┌──────────────────────┐
                    │  Consolidated Data   │
                    │  - JSON (2.2 MB)     │
                    │  - CSV (2.0 MB)      │
                    │  5,000 products      │
                    └──────────────────────┘
                               │
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Dashboard View     │
                    │   http://server:8080 │
                    └──────────────────────┘
```

## Current Status (December 17, 2025)

### Running Services

1. **Dashboard** ✅
   - URL: http://172.173.144.149:8080
   - Password: `admin123`
   - PID: 38991
   - Status: Running

2. **Auto-Fetch Service** ✅
   - PID: 40574
   - Status: Running
   - Check Interval: Every 5 minutes
   - Last Run: Successfully downloaded 5,000 products

3. **GitHub Actions** ✅
   - Repository: mostafazog/MRO-Supply
   - Workers: 50 parallel jobs
   - Status: Ready to trigger from dashboard

4. **Azure Functions** ✅
   - URL: https://mrosupply-scraper-func.azurewebsites.net
   - Workers: 100+ concurrent
   - Status: Deployed and ready

### Data Collection

- **Total Products Scraped**: 5,000 unique products
- **Duplicates Removed**: 10,000
- **Output Files**:
  - `consolidated_data/consolidated_products.json` (2.2 MB)
  - `consolidated_data/consolidated_products.csv` (2.0 MB)

## Cost Savings

| Component | Old Cost | New Cost | Savings |
|-----------|----------|----------|---------|
| GitHub Actions | $0 (FREE) | $0 (FREE) | $0 |
| Azure Functions | $0 (FREE tier) | $0 (FREE tier) | $0 |
| Webshare Proxies | $2,000-3,000 | $0 (NOT NEEDED!) | **$2,000-3,000** |
| **TOTAL** | **$2,000-3,000** | **$0** | **$2,000-3,000** |

**Why No Proxies?** GitHub Actions and Azure Functions both provide dynamic IPs automatically!

## How to Use

### 1. Trigger New Scraping Run

**From Dashboard:**
1. Go to http://172.173.144.149:8080
2. Login with password: `admin123`
3. Click **Monitor** tab
4. Click **Trigger Workflow** button
5. Confirm the dialog
6. Watch progress in GitHub Actions section

**From Command Line:**
```bash
# Trigger workflow manually
curl -X POST \
  -H "Authorization: token ghp_YOUR_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/mostafazog/MRO-Supply/actions/workflows/distributed-scrape-azure.yml/dispatches \
  -d '{"ref":"main","inputs":{"total_products":"1508714","batch_size":"100","use_azure_functions":"true","github_workers":"50"}}'
```

### 2. Monitor Progress

**Dashboard:**
- Monitor tab shows real-time status of GitHub Actions and Azure Functions
- Auto-refreshes every 15 seconds
- Shows last 3 workflow runs with status

**Logs:**
```bash
# Dashboard logs
ssh azureuser@172.173.144.149 "tail -f ~/mrosupply-scraper/dashboard.log"

# Auto-fetch service logs
ssh azureuser@172.173.144.149 "tail -f ~/mrosupply-scraper/auto_fetch.log"
```

### 3. Access Scraped Data

**Automatic:** Data is automatically downloaded every 5 minutes to:
- `~/mrosupply-scraper/consolidated_data/consolidated_products.json`
- `~/mrosupply-scraper/consolidated_data/consolidated_products.csv`

**Download to Local:**
```bash
# Download consolidated CSV
scp azureuser@172.173.144.149:~/mrosupply-scraper/consolidated_data/consolidated_products.csv .

# Download consolidated JSON
scp azureuser@172.173.144.149:~/mrosupply-scraper/consolidated_data/consolidated_products.json .
```

**From GitHub:**
```bash
# Direct download from GitHub Actions artifacts
export GITHUB_TOKEN="your_token"
python3 fetch_github_data.py
python3 consolidate_data.py
```

## Service Management

### Dashboard

```bash
# Check status
ssh azureuser@172.173.144.149 "pgrep -f enhanced_dashboard.py"

# Restart dashboard
ssh azureuser@172.173.144.149 "cd ~/mrosupply-scraper && pkill -f enhanced_dashboard.py && nohup python3 enhanced_dashboard.py > dashboard.log 2>&1 &"

# View logs
ssh azureuser@172.173.144.149 "tail -f ~/mrosupply-scraper/dashboard.log"
```

### Auto-Fetch Service

```bash
# Check status
ssh azureuser@172.173.144.149 "ps aux | grep auto_fetch_service.py | grep -v grep"

# View logs
ssh azureuser@172.173.144.149 "tail -f ~/mrosupply-scraper/auto_fetch.log"

# Stop service
ssh azureuser@172.173.144.149 "pkill -f auto_fetch_service.py"

# Start service
ssh azureuser@172.173.144.149 "cd ~/mrosupply-scraper && export GITHUB_TOKEN='your_token' && nohup python3 auto_fetch_service.py > auto_fetch_output.log 2>&1 &"
```

## Features

### Dashboard Features
- ✅ Real-time scraper monitoring
- ✅ GitHub Actions workflow status
- ✅ Azure Functions health monitoring
- ✅ System metrics (CPU, memory, disk)
- ✅ Log viewer with real-time updates
- ✅ Clear logs button
- ✅ File browser and download
- ✅ One-click workflow triggering
- ✅ Auto-refresh (15 seconds)

### Auto-Fetch Service Features
- ✅ Automatic artifact downloading
- ✅ Smart deduplication
- ✅ JSON and CSV export
- ✅ State tracking (no re-downloads)
- ✅ Full activity logging
- ✅ Background operation (24/7)
- ✅ Automatic consolidation
- ✅ Error handling and retry

### Distributed Scraping Features
- ✅ 150+ parallel workers (50 GitHub + 100+ Azure)
- ✅ Dynamic IP rotation (no proxies!)
- ✅ Automatic scaling
- ✅ Fault tolerance
- ✅ Progress tracking
- ✅ Failed URL retry
- ✅ Checkpoint system

## Troubleshooting

### Dashboard Not Accessible

```bash
# Check if running
ssh azureuser@172.173.144.149 "pgrep -f enhanced_dashboard.py"

# Check port
ssh azureuser@172.173.144.149 "netstat -tulpn | grep 8080"

# Check logs for errors
ssh azureuser@172.173.144.149 "tail -100 ~/mrosupply-scraper/dashboard.log | grep ERROR"
```

### Auto-Fetch Not Working

```bash
# Check if running
ssh azureuser@172.173.144.149 "ps aux | grep auto_fetch_service.py"

# Check logs
ssh azureuser@172.173.144.149 "tail -100 ~/mrosupply-scraper/auto_fetch.log | grep ERROR"

# Restart service
ssh azureuser@172.173.144.149 "pkill -f auto_fetch_service.py && cd ~/mrosupply-scraper && export GITHUB_TOKEN='your_token' && nohup python3 auto_fetch_service.py > auto_fetch_output.log 2>&1 &"
```

### No New Data

```bash
# Check if workflows are running
curl -H "Authorization: token your_token" \
  "https://api.github.com/repos/mostafazog/MRO-Supply/actions/runs?per_page=5"

# Check processed runs
ssh azureuser@172.173.144.149 "cat ~/mrosupply-scraper/processed_runs.json"

# Reset processed runs (will re-download everything)
ssh azureuser@172.173.144.149 "rm ~/mrosupply-scraper/processed_runs.json"
```

## Performance Metrics

### System Resources

- **CPU Usage**: <5% idle, 20-30% during scraping
- **Memory**: ~150 MB total (dashboard + auto-fetch)
- **Disk I/O**: Minimal, only during data fetching
- **Network**: Only during artifact downloads (every 5 min)

### Scraping Speed

- **GitHub Actions**: 50 workers × 3 products/worker/batch = 150 products/batch
- **Azure Functions**: 100 workers × 100 products/hour = 10,000 products/hour
- **Combined**: ~10,000-15,000 products per run
- **Total Target**: 1,508,714 products (~100-150 runs needed)

## Next Steps

### Recommended Actions

1. **Monitor First Run**: Watch the dashboard and logs for the first complete run
2. **Verify Data Quality**: Check consolidated CSV for data completeness
3. **Adjust Workers**: If needed, modify GitHub Actions matrix for more/less workers
4. **Set Up Alerts**: Add email notifications for completion (optional)
5. **Schedule Runs**: Set up cron job to trigger workflows automatically (optional)

### Optional Enhancements

```bash
# Add cron job for automatic daily scraping
crontab -e
# Add: 0 2 * * * curl -X POST -H "Authorization: token YOUR_TOKEN" https://api.github.com/repos/mostafazog/MRO-Supply/actions/workflows/distributed-scrape-azure.yml/dispatches -d '{"ref":"main"}'

# Add email notifications
# Edit auto_fetch_service.py and add SMTP configuration

# Increase auto-fetch frequency
# Edit auto_fetch_service.py: CHECK_INTERVAL = 180  # 3 minutes
```

## Documentation

- **Dashboard Guide**: [DASHBOARD_ACCESS.md](DASHBOARD_ACCESS.md)
- **Auto-Fetch Guide**: [AUTO_FETCH_README.md](AUTO_FETCH_README.md)
- **Data Fetching**: [FETCH_DATA_README.md](FETCH_DATA_README.md)
- **Deployment**: [deploy_enhanced_dashboard.sh](deploy_enhanced_dashboard.sh)

## Support

For issues:
1. Check service logs
2. Verify environment variables
3. Check GitHub Actions workflow status
4. Verify Azure Functions are deployed

## Summary

You now have a **completely automated** web scraping system:

✅ **Dashboard**: Real-time monitoring and control
✅ **Auto-Fetch**: Automatic data collection (24/7)
✅ **Distributed**: 150+ parallel workers
✅ **Cost**: $0 (no proxy costs!)
✅ **Data**: Automatically consolidated into CSV/JSON

**Just trigger the workflow from the dashboard and let it run!** 🚀
