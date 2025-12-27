# Raptor Supplies - GitHub Actions Scraping Guide

## Overview

Use GitHub Actions to scrape RaptorSupplies.com with distributed workers, bypassing Cloudflare protection using browser automation in the cloud.

## 🚀 Setup

### 1. Commit Required Files

```bash
# Make sure these files are in your repo:
git add raptorsupplies_urls.json
git add raptorsupplies_github_worker.py
git add raptorsupplies_aggregate.py
git add .github/workflows/scrape-raptorsupplies.yml
git commit -m "Add Raptor Supplies GitHub Actions scraper"
git push
```

### 2. Run Workflow

1. Go to your GitHub repo
2. Click **Actions** tab
3. Select **"Scrape Raptor Supplies"** workflow
4. Click **"Run workflow"**
5. Configure parameters:
   - **Total products:** How many to scrape (max 89,155)
   - **Workers:** Number of parallel workers (1-10)
   - **Start index:** Where to start in URL list (default: 0)
   - **Use browser:** Enable Cloudflare bypass (recommended: true)

## 📊 Parameters Explained

### Total Products
- **Small test:** 100 products (~10 minutes)
- **Medium batch:** 1,000 products (~1-2 hours)
- **Large batch:** 10,000 products (~10-20 hours)
- **Full catalog:** 89,155 products (~90+ hours)

### Workers
- **1 worker:** Sequential processing (slowest)
- **5 workers:** Good balance (recommended)
- **10 workers:** Maximum parallelization (fastest)

⚠️ **Note:** GitHub Actions has concurrent job limits on free tier

### Browser Mode
- **true:** Use Selenium + Chrome (bypasses Cloudflare, slower)
- **false:** Direct HTTP requests (faster but blocked by Cloudflare)

**Recommendation:** Always use `true` for RaptorSupplies

## 🎯 Usage Examples

### Example 1: Small Test (10 minutes)
```yaml
Total products: 100
Workers: 5
Start index: 0
Use browser: true
```

### Example 2: Medium Batch (2 hours)
```yaml
Total products: 1000
Workers: 10
Start index: 0
Use browser: true
```

### Example 3: Large Batch (1 day)
```yaml
Total products: 10000
Workers: 10
Start index: 0
Use browser: true
```

### Example 4: Resume from Checkpoint
If you scraped 5,000 products and want to continue:
```yaml
Total products: 5000
Workers: 10
Start index: 5000  # Start from where you left off
Use browser: true
```

## 📥 Downloading Results

After workflow completes:

1. Go to workflow run page
2. Scroll to **Artifacts** section
3. Download:
   - `final-results` - Contains all scraped products
   - `worker-X-results` - Individual worker results (for debugging)

## 📁 Result Files

### final-results artifact:
- **raptor_products_final.json** - All scraped products
- **raptor_scraping_summary.json** - Statistics

### Individual worker artifacts:
- **worker_0_products.json** - Products from worker 0
- **worker_0_errors.json** - Errors from worker 0
- (Same for workers 1-9)

## 🔧 Advanced Configuration

### Scrape Specific Range

To scrape products 10,000 to 20,000:
```yaml
Total products: 10000
Workers: 10
Start index: 10000
Use browser: true
```

### Maximum Speed

For fastest scraping (may hit rate limits):
```yaml
Total products: 1000
Workers: 10
Start index: 0
Use browser: true
```

Adjust delays in `raptorsupplies_github_worker.py` line ~290:
```python
delay = random.uniform(3, 5)  # Reduce from 5-10 to 3-5
```

### Multiple Runs Strategy

For scraping all 89K products, split into multiple runs:

**Run 1:**
```yaml
Total: 10000, Start: 0
```

**Run 2:**
```yaml
Total: 10000, Start: 10000
```

**Run 3:**
```yaml
Total: 10000, Start: 20000
```

... and so on

## 📊 Monitoring Progress

### Check Workflow Status

In GitHub Actions:
- ✅ Green checkmark = Success
- ❌ Red X = Failed
- 🟡 Yellow circle = Running

### View Logs

Click on workflow run → Click on job → View step logs

Look for:
```
🤖 Worker X initialized
📋 Loaded 89,155 URLs
✅ Browser initialized
[1/100] https://www.raptorsupplies.com/...
   ✅ Product Name Here
```

### Summary Output

At the end of workflow, you'll see:
```
## 🎉 Scraping Complete

- **Total Products:** 950
- **Successful:** 950
- **Failed:** 50
- **Success Rate:** 95.0%
```

## ⚠️ Limitations

### GitHub Actions Free Tier
- **2,000 minutes/month** for private repos
- **Unlimited** for public repos
- **Concurrent jobs:** 20 (varies by plan)

### Timeouts
- **Maximum job runtime:** 6 hours
- **Recommendation:** Keep batches under 5 hours

### Rate Limiting
- Cloudflare may still block aggressive scraping
- Use delays (5-10 seconds between requests)
- If blocked, increase delays

## 🐛 Troubleshooting

### Problem: All workers failing with 403
**Solution:** Cloudflare is blocking. Options:
1. Increase delays between requests
2. Use fewer workers (reduce to 3-5)
3. Use residential proxies
4. Consider paid service (ScraperAPI)

### Problem: Workers timeout after 6 hours
**Solution:** Reduce batch size:
```yaml
Total products: 5000  # Instead of 10000
```

### Problem: No artifacts generated
**Solution:** Check logs for errors:
1. Click on failed workflow
2. View job logs
3. Look for Python errors

### Problem: Browser fails to initialize
**Solution:** May need to update Chrome installation in workflow:
```yaml
- name: Install Chrome
  run: |
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
    sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list'
    sudo apt-get update
    sudo apt-get install -y google-chrome-stable
```

### Problem: High failure rate
**Solution:** Check if selectors need updating:
1. Download sample failed product
2. View HTML structure
3. Update selectors in `raptorsupplies_github_worker.py`

## 💡 Best Practices

### 1. Start Small
Always test with 100 products first:
```yaml
Total products: 100
Workers: 5
```

### 2. Monitor First Run
Watch the logs to ensure:
- Browser initializes successfully
- Cloudflare challenge passes
- Products are extracted correctly

### 3. Gradual Scale-Up
- Test: 100 products
- Small: 1,000 products
- Medium: 5,000 products
- Large: 10,000+ products

### 4. Save Frequently
Run multiple smaller batches instead of one huge batch:
- Easier to recover from failures
- Can monitor progress
- Less likely to timeout

### 5. Off-Peak Hours
Schedule runs during off-peak:
- Night time (US timezone)
- Weekends
- Less likely to be rate-limited

## 📈 Performance Estimates

Based on 10 workers with browser mode:

| Products | Estimated Time | GitHub Minutes Used |
|----------|----------------|---------------------|
| 100      | 10 minutes     | 100 (10×10)        |
| 1,000    | 1.5 hours      | 900 (10×90)        |
| 5,000    | 8 hours        | 4,800              |
| 10,000   | 16 hours       | 9,600              |
| 89,155   | ~140 hours     | 84,000             |

⚠️ **Free tier limit:** 2,000 minutes/month (private repos)

**Recommendation:** For full catalog, use multiple accounts or paid GitHub plan

## 🔐 Security Best Practices

### Don't Commit Sensitive Data
```bash
# Add to .gitignore
*.log
*_errors.json
artifacts/
```

### Use GitHub Secrets
For API keys or credentials:
1. Go to repo Settings → Secrets
2. Add secret (e.g., `SCRAPER_API_KEY`)
3. Use in workflow: `${{ secrets.SCRAPER_API_KEY }}`

## 🎓 Comparison with Other Methods

| Method | Cost | Speed | Reliability | Cloudflare Bypass |
|--------|------|-------|-------------|-------------------|
| GitHub Actions | Free* | Medium | Good | ✅ Yes (browser) |
| ScraperAPI | $49/mo | Fast | Excellent | ✅ Yes |
| Local Selenium | Free | Slow | Fair | ✅ Yes |
| Local HTTP | Free | Fast | Poor | ❌ No |

*Free for public repos, 2000 min/month for private

## 📞 Support

If issues persist:
1. Check workflow logs
2. Test locally first: `python raptorsupplies_github_worker.py`
3. Review error artifacts
4. Adjust parameters

## 🚀 Quick Start Command

```bash
# 1. Commit files
git add .
git commit -m "Setup Raptor Supplies scraper"
git push

# 2. Go to GitHub → Actions → "Scrape Raptor Supplies" → Run workflow

# 3. Set parameters:
#    Total: 100
#    Workers: 5
#    Browser: true

# 4. Download results when done
```

Good luck! 🎉
