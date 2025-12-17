# Fetching Scraped Data from GitHub Actions & Azure Functions

## Overview

Your distributed scraping system uses:
- **GitHub Actions**: 50 parallel workers (no proxies, dynamic IPs)
- **Azure Functions**: 100+ auto-scaling workers (no proxies, dynamic IPs)

Both save data to **GitHub Actions artifacts** which you can download.

## Quick Start

### 1. Fetch Data from GitHub Actions

```bash
python3 fetch_github_data.py
```

This will:
- Download all artifacts from recent workflow runs
- Extract JSON files with scraped products
- Save to `github_data/` directory
- Show total products downloaded

### 2. Check Azure Functions Status

```bash
python3 fetch_azure_data.py
```

This checks Azure Functions health. Note: Azure Functions data is collected by GitHub Actions and included in the artifacts downloaded in step 1.

### 3. Consolidate All Data

```bash
python3 consolidate_data.py
```

This will:
- Merge all JSON files from GitHub Actions artifacts
- Remove duplicates
- Create consolidated output files:
  - `consolidated_products.json` - JSON format
  - `consolidated_products.csv` - CSV format for Excel

## Complete Workflow

```bash
# Step 1: Download all data
python3 fetch_github_data.py

# Step 2: Consolidate into single file
python3 consolidate_data.py

# Step 3: View results
wc -l consolidated_products.csv
head -20 consolidated_products.csv
```

## Data Flow

```
GitHub Actions (50 workers)
       ↓
   Scrapes products → Saves to artifacts
       ↓
GitHub Actions orchestrator
       ↓
   Triggers → Azure Functions (100+ workers)
       ↓
   Azure scrapes products → Returns to GitHub Actions
       ↓
GitHub Actions collects all results → Saves to artifacts
       ↓
You download artifacts → Consolidate → Final CSV/JSON
```

## Monitoring Progress

### In Dashboard
1. Go to http://172.173.144.149:8080
2. Click "Monitor" tab
3. View GitHub Actions and Azure Functions status

### On GitHub
Visit: https://github.com/mostafazog/MRO-Supply/actions

See all workflow runs, download artifacts directly from the web UI.

## Current Architecture

✅ **No Webshare proxies** - Saves cost!
✅ **GitHub Actions** - Free dynamic IPs (50 workers)
✅ **Azure Functions** - Auto-scaling dynamic IPs (100+ workers)
✅ **Total**: 150+ parallel workers scraping 1.5M products

## Expected Output

After consolidation:
- `consolidated_products.json` - All unique products in JSON
- `consolidated_products.csv` - All unique products in CSV

Each product contains:
- title
- sku
- price
- description
- specifications
- images
- url
- ... and more fields

## Troubleshooting

**Q: No data in github_data/ directory?**
A: Make sure GITHUB_TOKEN is set in your environment or the script will use the hardcoded token.

**Q: How to check workflow progress?**
A: Visit https://github.com/mostafazog/MRO-Supply/actions or use your dashboard.

**Q: How long does scraping take?**
A: With 150 workers, approximately:
- 1.5M products / 150 workers = 10,000 products per worker
- ~2 seconds per product = ~20,000 seconds = ~5.5 hours

**Q: Can I run multiple workflows simultaneously?**
A: Yes! GitHub Actions supports multiple concurrent workflow runs.
