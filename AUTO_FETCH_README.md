# Auto-Fetch Service

Automated service that continuously monitors GitHub Actions and fetches scraped data automatically.

## Features

- **Automatic Monitoring**: Checks GitHub Actions every 5 minutes for new workflow runs
- **Smart Fetching**: Only downloads new artifacts (tracks processed runs)
- **Auto-Consolidation**: Automatically merges all data into single JSON/CSV files
- **Deduplication**: Removes duplicate products based on URL
- **Continuous Operation**: Runs as background service 24/7
- **Logging**: Full activity logs for monitoring and debugging

## Quick Start

### Option 1: Simple Background Service (Recommended)

```bash
# Start the service
./start_auto_fetch.sh

# Check logs
tail -f auto_fetch.log

# Stop the service
./stop_auto_fetch.sh
```

### Option 2: Systemd Service (Production)

```bash
# Copy service file
sudo cp auto-fetch.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Start service
sudo systemctl start auto-fetch

# Enable on boot
sudo systemctl enable auto-fetch

# Check status
sudo systemctl status auto-fetch

# View logs
sudo journalctl -u auto-fetch -f
```

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                   Auto-Fetch Service Loop                    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
              ┌─────────────────────────┐
              │  Check GitHub Actions   │
              │  for new workflow runs  │
              └────────────┬────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │  New runs found?        │
              └────────┬────────┬───────┘
                       │        │
                   No  │        │  Yes
                       │        │
                       │        ▼
                       │  ┌─────────────────────┐
                       │  │  Download artifacts │
                       │  │  (ZIP files)        │
                       │  └──────────┬──────────┘
                       │             │
                       │             ▼
                       │  ┌─────────────────────┐
                       │  │  Extract JSON files │
                       │  │  Save to github_data│
                       │  └──────────┬──────────┘
                       │             │
                       │             ▼
                       │  ┌─────────────────────┐
                       │  │  Mark run as        │
                       │  │  processed          │
                       │  └──────────┬──────────┘
                       │             │
                       │             ▼
                       │  ┌─────────────────────┐
                       │  │  Consolidate all    │
                       │  │  data into single   │
                       │  │  JSON/CSV files     │
                       │  └──────────┬──────────┘
                       │             │
                       └─────────────┴──────────┐
                                                 │
                                                 ▼
                              ┌─────────────────────────┐
                              │  Wait 5 minutes         │
                              └────────────┬────────────┘
                                           │
                                           │ (loop back)
                                           └─────────┐
                                                     │
                              ┌──────────────────────┘
                              │
                              ▼
                    (Repeat Forever)
```

## Directory Structure

```
mrosupply-scraper/
├── auto_fetch_service.py      # Main service script
├── start_auto_fetch.sh        # Easy start script
├── stop_auto_fetch.sh         # Easy stop script
├── auto-fetch.service         # Systemd service file
├── auto_fetch.log             # Service activity log
├── auto_fetch_output.log      # Service stdout/stderr
├── auto_fetch.pid             # Process ID file
├── processed_runs.json        # Tracks processed GitHub runs
├── github_data/               # Downloaded artifacts
│   ├── run_1/
│   ├── run_2/
│   └── run_3/
└── consolidated_data/         # Final merged output
    ├── consolidated_products.json
    └── consolidated_products.csv
```

## Configuration

Edit `auto_fetch_service.py` to customize:

```python
# Check interval (seconds)
CHECK_INTERVAL = 300  # 5 minutes

# Repository
REPO = 'mostafazog/MRO-Supply'

# Output directories
OUTPUT_DIR = Path('github_data')
CONSOLIDATED_DIR = Path('consolidated_data')
```

## Monitoring

### Check Service Status

```bash
# If using simple background service
ps aux | grep auto_fetch_service.py

# If using systemd
sudo systemctl status auto-fetch
```

### View Logs

```bash
# Real-time log tail
tail -f auto_fetch.log

# View full log
cat auto_fetch.log

# Last 100 lines
tail -100 auto_fetch.log

# Search for errors
grep ERROR auto_fetch.log
```

### Check Consolidated Data

```bash
# View consolidated products
ls -lh consolidated_data/

# Count products in JSON
cat consolidated_data/consolidated_products.json | python3 -c "import sys, json; print(f'{len(json.load(sys.stdin)):,} products')"

# View CSV in terminal
head consolidated_data/consolidated_products.csv
```

## Troubleshooting

### Service Won't Start

```bash
# Check Python is available
python3 --version

# Check dependencies
pip3 install requests

# Check GitHub token
echo $GITHUB_TOKEN

# Run manually to see errors
python3 auto_fetch_service.py
```

### No Data Being Fetched

```bash
# Check if GitHub Actions has completed runs
curl -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/mostafazog/MRO-Supply/actions/runs?per_page=5"

# Check processed runs
cat processed_runs.json

# Reset processed runs (will re-download everything)
rm processed_runs.json
```

### Service Crashes

```bash
# Check logs for errors
tail -50 auto_fetch.log

# Restart service
./stop_auto_fetch.sh
./start_auto_fetch.sh

# If using systemd
sudo systemctl restart auto-fetch
```

## Performance

- **CPU Usage**: <5% (mostly idle, waiting)
- **Memory**: ~50-100 MB
- **Disk I/O**: Only during fetching (every 5 minutes)
- **Network**: Only downloads new artifacts
- **Efficiency**: Tracks processed runs to avoid re-downloading

## Features vs Manual Fetching

| Feature | Manual | Auto-Fetch Service |
|---------|--------|-------------------|
| Monitoring | Manual checking | Automatic every 5 min |
| Downloading | Run script manually | Automatic |
| Consolidation | Run script manually | Automatic |
| Deduplication | Manual | Automatic |
| 24/7 Operation | No | Yes |
| Logging | No | Full activity log |
| State Tracking | No | Tracks processed runs |

## Integration with Dashboard

The auto-fetch service works alongside your dashboard:

1. **Dashboard**: Real-time monitoring of GitHub Actions and Azure Functions
2. **Auto-Fetch**: Automatic downloading and consolidation of results
3. **Combined**: Complete automation - trigger workflows from dashboard, data automatically collected

## Cost Savings

- **GitHub Actions**: 50 workers with dynamic IPs (FREE)
- **Azure Functions**: 100+ workers with dynamic IPs (FREE tier)
- **Auto-Fetch**: Local service (FREE)
- **Total Proxy Costs**: $0 (vs $2,000-3,000 with Webshare)

## Advanced Usage

### Change Check Interval

Edit `auto_fetch_service.py`:

```python
CHECK_INTERVAL = 600  # Check every 10 minutes
CHECK_INTERVAL = 60   # Check every 1 minute (more aggressive)
```

### Custom Processing

Add custom logic in `auto_fetch_service.py`:

```python
def custom_processing(self, products):
    """Add your custom processing here"""
    # Filter products
    filtered = [p for p in products if p.get('price')]

    # Add custom fields
    for p in filtered:
        p['fetched_at'] = datetime.now().isoformat()

    return filtered
```

### Email Notifications

Add email alerts when new data is found:

```python
import smtplib

def send_notification(self, product_count):
    """Send email when new products found"""
    # Your email logic here
    pass
```

## Support

For issues or questions:
1. Check logs: `tail -f auto_fetch.log`
2. Check GitHub Actions: https://github.com/mostafazog/MRO-Supply/actions
3. Verify service is running: `ps aux | grep auto_fetch_service.py`

## Summary

The auto-fetch service provides **complete automation**:
- ✅ No manual intervention needed
- ✅ Runs 24/7 in background
- ✅ Automatically downloads new data
- ✅ Consolidates into single file
- ✅ Removes duplicates
- ✅ Full activity logging
- ✅ Works with dashboard

**Set it and forget it!**
