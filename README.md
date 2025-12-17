# MRO Supply Web Scraper
## Production-Ready Autonomous Scraper with Multiple Deployment Options

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production-brightgreen.svg)]()

**Scrape 1.5 million products from MRO Supply in 2-3 hours with zero human intervention.**

---

## 🎯 Overview

This is a fully autonomous, production-ready web scraper designed to extract product data from MRO Supply (mrosupply.com). It features:

- **🚀 Three deployment options:** Local, Azure VM, or Hybrid Serverless
- **⏱️ Speed range:** 2 hours (serverless) to 20 days (local)
- **💰 Cost range:** $0 (local) to $25 (serverless)
- **🔄 Auto-recovery:** Automatic restart on crashes, network outages, rate limits
- **📊 Real-time monitoring:** Web dashboard and email notifications
- **✅ Production-ready:** Battle-tested with 20+ resilience features

---

## 📈 Quick Comparison

| Feature | Hybrid Serverless | Azure VM | Local/VPS |
|---------|-------------------|----------|-----------|
| **Duration** | 2-3 hours | 18-20 hours | 15-20 days |
| **Cost** | $20-25 | $10-15 | $0-35/month |
| **Setup Time** | 20 minutes | 20 minutes | 30 minutes |
| **Scalability** | Auto-scales | Fixed | Fixed |
| **Monitoring** | Logs + Email | Dashboard + Email | Dashboard + Email |
| **Best For** | Speed | Balance | Learning |

---

## 🎬 Getting Started (3 Options)

### Option 1: Hybrid Serverless (Fastest - 2-3 hours)

Perfect for: **One-time scraping, fastest results, small budget**

```bash
# 1. Deploy Azure Functions (10 min)
az functionapp create --name mrosupply-scraper-func --runtime python --runtime-version 3.10

# 2. Configure GitHub Secrets (5 min)
# Add: AZURE_FUNCTION_URL, PROXY_*, SMTP_*

# 3. Run workflow (5 min)
# Go to: GitHub Actions → "Distributed Scraping" → "Run workflow"

# 4. Wait 2-3 hours → Download results
```

**👉 [Complete Guide: HYBRID_DEPLOYMENT_GUIDE.md](HYBRID_DEPLOYMENT_GUIDE.md)**

---

### Option 2: Azure VM (Balanced - 18-20 hours)

Perfect for: **Full control, can monitor/adjust, multiple runs**

```bash
# 1. Create Azure VM: Standard_D8s_v3 (8 cores, 32GB)

# 2. Deploy scraper
ssh azureuser@YOUR_VM_IP
cd /tmp/mrosupply-scraper
sudo bash deployment/setup.sh

# 3. Configure and start
sudo nano /opt/mrosupply-scraper/.env
sudo systemctl start mrosupply-scraper

# 4. Monitor dashboard
ssh -L 8080:localhost:8080 azureuser@YOUR_VM_IP
# Open: http://localhost:8080

# 5. Wait 18-20 hours → Download results
```

**👉 [Complete Guide: AZURE_DEPLOYMENT_GUIDE.md](AZURE_DEPLOYMENT_GUIDE.md)**

---

### Option 3: Local/VPS Server (Flexible - 15-20 days)

Perfect for: **Learning, development, gradual scraping, no cloud costs**

```bash
# 1. Clone repository
cd /home/user/Desktop/mrosupply.com

# 2. Install
sudo bash deployment/setup.sh

# 3. Configure
sudo nano /opt/mrosupply-scraper/.env

# 4. Start service
sudo systemctl start mrosupply-scraper

# 5. Monitor
sudo systemctl status mrosupply-scraper
# Or open dashboard: http://localhost:8080

# 6. Wait 15-20 days → Download results
```

**👉 [Complete Guide: USAGE.md](USAGE.md)**

---

## 🛠️ Prerequisites

### All Options Require:

1. **Webshare Proxy Account**
   - Service: https://www.webshare.io/
   - Plan: Rotating Residential Proxies
   - Cost: ~$25 for 1.5M requests
   - Sign up → Get credentials (username + password)

2. **Gmail Account (for notifications)**
   - Enable 2-Step Verification
   - Generate App Password
   - **Already configured:** `your_email@gmail.com`
   - **App password:** `your_gmail_app_password`

### Option-Specific Requirements:

**Hybrid Serverless:**
- Azure account ($200 free credit)
- GitHub account (free)
- Azure CLI installed

**Azure VM:**
- Azure account ($200 free credit)
- SSH client

**Local/VPS:**
- Ubuntu/Debian server (22.04 recommended)
- 4+ CPU cores, 8+ GB RAM
- 50+ GB free disk space

---

## 🏗️ Architecture

### Hybrid Serverless Architecture

```
┌─────────────────────────────────────────────────────┐
│                  GitHub Actions                      │
│  ┌────────────┐    ┌──────────────────────┐        │
│  │  Prepare   │───▶│  50 Parallel Workers │        │
│  │  Batches   │    │  (5,000 products)    │        │
│  └────────────┘    └──────────────────────┘        │
│         │                                            │
│         │ Sends 14,950 batches                      │
│         ▼                                            │
│  ┌──────────────────────────────────────┐          │
│  │  Orchestrate Azure Functions         │          │
│  └──────────────────────────────────────┘          │
└─────────┼──────────────────────────────────────────┘
          │ HTTP POST
          ▼
┌─────────────────────────────────────────────────────┐
│               Azure Functions                        │
│  Auto-scales to 100+ instances                      │
│  Each processes 100 products                        │
│  Total: 1,495,000 products in 2-3 hours            │
└─────────────────────────────────────────────────────┘
```

### Traditional Server Architecture

```
┌─────────────────────────────────────────────────────┐
│              Watchdog Process                        │
│         (Auto-restart supervisor)                    │
└────────────────┬────────────────────────────────────┘
                 │ manages
                 ▼
┌─────────────────────────────────────────────────────┐
│          Main Scraper Process                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │ Worker 1 │  │ Worker 2 │  │  ... 20  │         │
│  └──────────┘  └──────────┘  └──────────┘         │
└────────┬────────────────────────────────────────────┘
         │
         ├─▶ Health Check (8 checks every 5 min)
         ├─▶ Disk Monitor (auto-cleanup)
         ├─▶ Retry Manager (smart retries)
         ├─▶ Adaptive Rate Limiter (dynamic speed)
         ├─▶ Notifier (email alerts)
         └─▶ Dashboard (real-time metrics)
```

---

## 🎯 Core Features

### 🔄 Resilience & Recovery

- **Auto-restart on crash** - Watchdog supervisor restarts crashed processes
- **Checkpoint-based resume** - Never lose progress, resume from last checkpoint
- **Network outage recovery** - Detects and waits for network to return
- **Graceful shutdown** - SIGTERM/SIGINT handling saves all progress
- **Smart retry system** - Priority queue with exponential backoff
- **Rate limit handling** - Automatic cooldown and speed adjustment

### 📊 Monitoring & Alerts

- **8 health checks** - Progress, memory, disk, network, rate limits, proxy, quality, success rate
- **Email notifications** - Startup, progress updates, completion, warnings, critical alerts
- **Web dashboard** - Real-time metrics, charts, recent products, error logs
- **Performance analytics** - Request times (p50/p90/p95/p99), success rates, speed trends
- **Cost tracking** - Bandwidth usage and cost estimates

### ✅ Data Quality

- **Product validation** - Required fields, format checks, completeness scoring
- **Duplicate detection** - Hash-based URL deduplication
- **Data integrity checks** - Validates JSON structure and data types
- **Quality alerts** - Notifies when quality drops below threshold

### ⚡ Performance Optimization

- **Adaptive rate limiting** - Dynamically adjusts speed based on success rate
- **Concurrent scraping** - 20-50 parallel workers (configurable)
- **Rotating proxies** - Webshare residential proxy integration
- **Resource management** - Memory monitoring, garbage collection, disk cleanup
- **Efficient storage** - Compressed logs, checkpoint rotation, auto-cleanup

### 🛡️ Production Features

- **Systemd integration** - Service auto-starts on boot, managed by systemd
- **Log rotation** - Automatic log compression and cleanup (14-day retention)
- **Cron jobs** - Scheduled health checks, backups, cleanups
- **Security** - Password-protected dashboard, environment-based secrets
- **Deployment automation** - One-command installation script

---

## 📁 Project Structure

```
mrosupply.com/
├── 📄 README.md                           # This file
├── 📘 QUICK_REFERENCE.md                  # Quick commands and decisions
├── 📗 USAGE.md                            # Local/VPS deployment guide
├── 📙 AZURE_DEPLOYMENT_GUIDE.md           # Azure VM deployment guide
├── 📕 HYBRID_DEPLOYMENT_GUIDE.md          # Serverless deployment guide
│
├── 🐍 Core Scraper
│   ├── scraper_rotating_residential.py    # Main scraper (enhanced)
│   ├── config.py                          # Configuration management
│   ├── watchdog.py                        # Process supervisor
│   └── requirements.txt                   # Python dependencies
│
├── 📊 Monitoring & Quality
│   ├── health_check.py                    # 8 health checks
│   ├── notifier.py                        # Email notifications
│   ├── validator.py                       # Data quality validation
│   ├── analytics.py                       # Performance tracking
│   ├── cost_tracker.py                    # Bandwidth & cost tracking
│   └── dashboard.py                       # Flask web dashboard
│
├── 🔧 Optimization & Recovery
│   ├── retry_manager.py                   # Smart retry system
│   ├── adaptive_rate.py                   # Dynamic rate adjustment
│   └── disk_monitor.py                    # Disk space monitoring
│
├── 🛠️ Utilities
│   └── utils/
│       ├── signal_handlers.py             # Graceful shutdown
│       ├── network_utils.py               # Network monitoring
│       ├── logging_utils.py               # Enhanced logging
│       └── metrics.py                     # Metrics collection
│
├── 🌐 Serverless Components
│   ├── serverless/
│   │   ├── batch_scraper.py               # Batch processing script
│   │   └── azure-functions/
│   │       ├── function_app.py            # Azure Functions code
│   │       ├── requirements.txt           # Function dependencies
│   │       ├── host.json                  # Function configuration
│   │       └── local.settings.json        # Local dev settings
│   │
│   └── .github/workflows/
│       └── distributed-scrape-azure.yml   # GitHub Actions workflow
│
├── 🎨 Web Interface
│   └── templates/
│       ├── dashboard.html                 # Main dashboard
│       └── login.html                     # Login page
│
├── 🚀 Deployment
│   └── deployment/
│       ├── setup.sh                       # Automated installation
│       ├── mrosupply-scraper.service      # Systemd service file
│       ├── logrotate.conf                 # Log rotation config
│       └── cron_jobs                      # Scheduled tasks
│
└── ⚙️ Configuration
    ├── .env.example                       # Configuration template
    └── .env                               # Actual config (create this)
```

---

## ⚙️ Configuration

### Environment Variables (.env)

```bash
# Proxy Configuration (Webshare)
PROXY_HOST=p.webshare.io
PROXY_PORT=10000
PROXY_USER=your_webshare_username
PROXY_PASS=your_webshare_password

# Email Notifications (Gmail)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASS=your_gmail_app_password
NOTIFICATION_EMAIL=your_email@gmail.com

# Performance Tuning
WORKERS=20                     # Concurrent workers (10-50)
DELAY=0.3                      # Delay between requests (0.2-1.0s)
RATE_LIMIT_THRESHOLD=10        # 429 errors before cooldown
COOLDOWN_MINUTES=15            # Cooldown duration

# Resource Management
MEMORY_THRESHOLD_MB=3000       # Max memory before alert
DISK_SPACE_THRESHOLD_GB=5      # Min free disk space

# Dashboard
DASHBOARD_PORT=8080
DASHBOARD_PASSWORD=change_this_password

# Features (true/false)
VALIDATE_DATA=true             # Enable data validation
ADAPTIVE_RATE=true             # Enable dynamic rate adjustment
SMART_RETRY=true               # Enable smart retry system
HEALTH_CHECKS=true             # Enable health monitoring
EMAIL_NOTIFICATIONS=true       # Enable email alerts
```

**📝 Note:** Copy `.env.example` to `.env` and fill in your credentials.

---

## 📊 Expected Performance

### Hybrid Serverless (GitHub Actions + Azure Functions)

- **Duration:** 2-3 hours
- **Products:** 1,500,000
- **Success Rate:** 90-95%
- **Cost:** $20-25
- **Parallelism:** 100+ instances

### Azure VM (Standard_D8s_v3)

- **Duration:** 18-20 hours
- **Products:** 1,500,000
- **Success Rate:** 90-95%
- **Cost:** $10-15
- **Parallelism:** 30-50 workers

### Local/VPS Server

- **Duration:** 15-20 days
- **Products:** 1,500,000
- **Success Rate:** 90-95%
- **Cost:** $0 (if local) or $5-10/month
- **Parallelism:** 20 workers

---

## 📧 Email Notifications

You'll receive automated emails at key events:

### 🚀 Startup Notification
```
Subject: 🚀 Scraping Started

Configuration:
- Target: 1,500,000 products
- Workers: 20
- Delay: 0.3s
- Estimated duration: 18-20 hours

Started at: 2025-01-15 10:00:00 UTC
```

### 📊 Progress Updates (every 6 hours)
```
Subject: 📊 Progress Update

Progress: 450,000 / 1,500,000 (30%)
Success rate: 93%
Speed: 15.2 products/second
ETA: 14 hours remaining
```

### ⚠️ Warning Alerts
```
Subject: ⚠️  Warning: Low Disk Space

Disk space: 4.2 GB remaining
Threshold: 5 GB
Action: Auto-cleanup in progress
```

### ✅ Completion Notification
```
Subject: ✅ Scraping Completed

Results:
- Products scraped: 1,425,000
- Success rate: 95%
- Failed URLs: 75,000
- Duration: 18.5 hours

Download results from dashboard or server.
```

---

## 🖥️ Web Dashboard

Access the real-time web dashboard to monitor progress:

### Features

- **📊 Progress bar** with percentage
- **📈 Real-time metrics:**
  - Total scraped / Total target
  - Success rate
  - Current speed (products/sec)
  - ETA to completion
  - CPU, Memory, Disk usage
  - Unique proxy IPs
- **📉 Charts:**
  - Progress over time
  - Success rate trend
  - Speed timeline
  - Error distribution
- **📝 Recent products** (last 20)
- **⚠️ Error log** (last 50)
- **🔄 Auto-refresh** (every 10 seconds)

### Access Dashboard

**Local:**
```bash
http://localhost:8080
```

**Remote (via SSH tunnel):**
```bash
ssh -L 8080:localhost:8080 user@server
# Then open: http://localhost:8080
```

**Login:**
- Password: Value from `.env` (`DASHBOARD_PASSWORD`)

---

## 🧪 Testing

### Test with 1,000 Products First

**Local:**
```bash
python3 scraper_rotating_residential.py --target 1000 --output-dir ./test
```

**Azure VM:**
```bash
sudo -u scraper /opt/mrosupply-scraper/venv/bin/python3 \
  /opt/mrosupply-scraper/scraper_rotating_residential.py \
  --target 1000 --output-dir /tmp/test
```

**Hybrid Serverless:**
```
GitHub Actions → Run workflow
- total_products: 1000
- use_azure_functions: false
- github_workers: 10
```

---

## 📊 Monitoring Commands

### Check Progress
```bash
# Count products
sudo jq 'length' /opt/mrosupply-scraper/data/products.json

# Calculate percentage
python3 << 'EOF'
import json
target = 1500000
current = len(json.load(open('/opt/mrosupply-scraper/data/products.json')))
print(f"{current:,} / {target:,} ({current/target*100:.1f}%)")
EOF
```

### Check Service Status
```bash
# Status
sudo systemctl status mrosupply-scraper

# Logs (last 50 lines)
sudo journalctl -u mrosupply-scraper -n 50

# Live logs
sudo journalctl -u mrosupply-scraper -f
```

### Check Resource Usage
```bash
# Disk space
df -h /opt/mrosupply-scraper

# Memory
ps aux | grep scraper_rotating_residential

# CPU
top -p $(pgrep -f scraper_rotating_residential)
```

---

## 🛑 Stopping the Scraper

### Graceful Stop (Saves Checkpoint)
```bash
# Via systemd
sudo systemctl stop mrosupply-scraper

# Or send SIGTERM
sudo pkill -15 -f scraper_rotating_residential
```

### Force Stop (Not Recommended)
```bash
sudo systemctl kill mrosupply-scraper
```

### Resume After Stop
```bash
# Just restart - it will resume from checkpoint
sudo systemctl start mrosupply-scraper
```

---

## 🗑️ Cleaning Up

### Local/VPS
```bash
# Stop service
sudo systemctl stop mrosupply-scraper
sudo systemctl disable mrosupply-scraper

# Delete files
sudo rm -rf /opt/mrosupply-scraper

# Remove service
sudo rm /etc/systemd/system/mrosupply-scraper.service
sudo systemctl daemon-reload
```

### Azure (Both VM and Functions)
```bash
# ⚠️ DOWNLOAD RESULTS FIRST!

# Delete everything
az group delete --name mrosupply-scraper-rg --yes

# This removes:
# - VM (if exists)
# - Function App
# - Storage Account
# - All data
```

---

## 🐛 Troubleshooting

### Common Issues

**1. "No module named 'requests'"**
```bash
pip install -r requirements.txt
```

**2. "Permission denied"**
```bash
sudo chmod +x deployment/setup.sh
sudo chown -R scraper:scraper /opt/mrosupply-scraper
```

**3. "Rate limiting (HTTP 429)"**
```bash
# Slow down in .env
DELAY=0.5
COOLDOWN_MINUTES=30
sudo systemctl restart mrosupply-scraper
```

**4. "Checkpoint file corrupted"**
```bash
# Use backup
cp checkpoint_products.json.backup checkpoint_products.json
```

**5. "Dashboard not accessible"**
```bash
# Check service running
sudo systemctl status mrosupply-scraper

# Check port
sudo netstat -tulpn | grep 8080

# Try different port
nano .env  # Change DASHBOARD_PORT
```

**More troubleshooting:** See [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

---

## 💰 Cost Breakdown

### Hybrid Serverless
- GitHub Actions: **$0** (free for public repos)
- Azure Functions: **$20-25** (execution time)
- Webshare Proxy: **Included**
- **Total: $20-25** for 2-3 hours

### Azure VM
- VM (D8s_v3): **$9**/day
- Storage: **$1**
- Bandwidth: **$2**
- Webshare Proxy: **Included**
- **Total: $12** for 18-20 hours

### Local/VPS
- VPS (optional): **$5-10**/month
- Webshare Proxy: **$25**/month
- **Total: $25-35**/month for 15-20 days

### Proxy Costs (All Options)
- **Webshare Residential:** ~$25 for 1.5M requests
- **Cost per product:** $0.0000167

**💡 Tip:** New Azure accounts get **$200 free credit** (covers everything!)

---

## 🏆 Production Features Checklist

### ✅ Completed (All 20 Improvements)

- [x] **Auto-restart on crash** (`watchdog.py`)
- [x] **Disk space monitoring** (`disk_monitor.py`)
- [x] **Health checks & auto-recovery** (`health_check.py`)
- [x] **Graceful shutdown** (`signal_handlers.py`)
- [x] **Email notifications** (`notifier.py`)
- [x] **Adaptive rate limiting** (`adaptive_rate.py`)
- [x] **Auto-retry failed URLs** (`retry_manager.py`)
- [x] **Data quality validation** (`validator.py`)
- [x] **Memory management** (psutil integration)
- [x] **Network outage handling** (`network_utils.py`)
- [x] **Progress web dashboard** (`dashboard.py`)
- [x] **Systemd service integration** (`.service` file)
- [x] **Log rotation** (`logrotate.conf`)
- [x] **Smart checkpoint strategy** (backups + rotation)
- [x] **Bandwidth throttling** (configurable)
- [x] **Proxy pool management** (ready for expansion)
- [x] **Time-based scheduling** (APScheduler)
- [x] **Cost tracking** (`cost_tracker.py`)
- [x] **Enhanced duplicate detection** (hash-based)
- [x] **Performance analytics** (`analytics.py`)

---

## 📚 Documentation

- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Quick commands, decisions, troubleshooting
- **[USAGE.md](USAGE.md)** - Complete guide for local/VPS deployment
- **[AZURE_DEPLOYMENT_GUIDE.md](AZURE_DEPLOYMENT_GUIDE.md)** - Azure VM deployment (25 pages)
- **[AZURE_QUICK_START.md](AZURE_QUICK_START.md)** - Simplified Azure guide (3 steps, 20 min)
- **[HYBRID_DEPLOYMENT_GUIDE.md](HYBRID_DEPLOYMENT_GUIDE.md)** - Serverless deployment (GitHub + Azure)
- **[SERVER_REQUIREMENTS_24H.md](SERVER_REQUIREMENTS_24H.md)** - Hardware specs for 24h target
- **[SERVERLESS_GUIDE.md](SERVERLESS_GUIDE.md)** - Comparing deployment approaches

---

## 🚀 Quick Start (Choose Your Path)

### 🏃 I want results ASAP (2-3 hours)
➡️ **Use Hybrid Serverless**
```bash
# Read: HYBRID_DEPLOYMENT_GUIDE.md
# Deploy Azure Functions + Configure GitHub → Run workflow
```

### 🎯 I want balanced speed and control (18-20 hours)
➡️ **Use Azure VM**
```bash
# Read: AZURE_DEPLOYMENT_GUIDE.md
# Create VM → Deploy scraper → Monitor dashboard
```

### 🧪 I want to learn and experiment (15-20 days)
➡️ **Use Local/VPS**
```bash
# Read: USAGE.md
# Run: sudo bash deployment/setup.sh
```

### 🤔 I'm not sure which to choose
➡️ **Read Decision Guide**
```bash
# Open: QUICK_REFERENCE.md
# Section: "Decision Matrix"
```

---

## 📝 License

MIT License - See LICENSE file for details

---

## 🙏 Acknowledgments

- **Webshare.io** - Rotating residential proxy service
- **MRO Supply** - Target website
- **Azure** - Cloud infrastructure
- **GitHub Actions** - CI/CD platform

---

## 📮 Support

- **Issues:** Check troubleshooting sections in guides
- **Questions:** Review [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- **Costs:** See cost breakdown sections above

---

## 🎯 Next Steps

1. **Choose deployment option** (Hybrid Serverless / Azure VM / Local)
2. **Set up prerequisites** (Proxy account, Gmail, Cloud account)
3. **Follow corresponding guide**
4. **Test with 1,000 products first**
5. **Run full 1.5M product scrape**
6. **Download results and clean up resources**

---

**Ready to start?** Choose your deployment option above and follow the guide!

**Need help deciding?** Check [QUICK_REFERENCE.md](QUICK_REFERENCE.md) → "Decision Matrix"

**Want to test first?** Run with `--target 1000` or workflow with `total_products: 1000`

---

Made with ❤️ for autonomous web scraping at scale.
