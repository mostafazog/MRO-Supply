# Complete Guide: Scraping RaptorSupplies.com

## Problem Summary

**raptorsupplies.com** has **very strict Cloudflare protection** that:
- Blocks automated requests (403 Forbidden)
- Requires JavaScript challenges
- Uses advanced bot detection
- Even headless browsers struggle to bypass

## ✅ Recommended Solutions (In Order of Easiest to Hardest)

### Solution 1: Manual Sitemap Download (EASIEST)

Since automation is blocked, manually download the sitemap:

#### Steps:
```bash
# 1. Open your regular browser (Firefox/Chrome)
# 2. Visit: https://www.raptorsupplies.com/robots.txt
# 3. Look for "Sitemap:" lines
# 4. Download each sitemap XML file
# 5. Save them locally

# Then parse them with this script:
```

Create `parse_local_sitemap.py`:
```python
#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import json

def parse_sitemap(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    urls = []
    for url in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
        loc = url.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
        if loc is not None and '/product' in loc.text.lower():
            urls.append(loc.text)

    return urls

# Parse your downloaded sitemap
product_urls = parse_sitemap('sitemap.xml')

# Save results
with open('raptorsupplies_urls.json', 'w') as f:
    json.dump({
        'total': len(product_urls),
        'urls': product_urls
    }, f, indent=2)

print(f"Found {len(product_urls)} products!")
```

### Solution 2: Browser Extension Scraping

Use a visual scraping tool:

#### Option A: Web Scraper Chrome Extension
1. Install: https://chrome.google.com/webstore/detail/web-scraper
2. Create sitemap manually
3. Extract product URLs
4. Export as CSV/JSON

#### Option B: Octoparse (Free tier available)
1. Download: https://www.octoparse.com/
2. Visual point-and-click scraping
3. Cloud scraping included
4. No coding required

### Solution 3: Paid Scraping Services (RECOMMENDED for automation)

These services handle Cloudflare automatically:

#### A. ScraperAPI (Best for developers)
```python
import requests

api_key = "YOUR_KEY"
url = "https://www.raptorsupplies.com/sitemap.xml"

response = requests.get(
    'http://api.scraperapi.com',
    params={
        'api_key': api_key,
        'url': url
    }
)

print(response.text)
```

**Pricing:**
- Free: 1,000 requests/month
- $49/month: 100,000 requests
- Website: https://www.scraperapi.com/

#### B. Bright Data (Formerly Luminati)
- Premium residential proxies
- Built-in Cloudflare bypass
- $500/month minimum
- Website: https://brightdata.com/

#### C. Zyte (Scrapy Cloud)
- Managed scraping infrastructure
- API + cloud platform
- $29/month starter plan
- Website: https://www.zyte.com/

### Solution 4: Playwright with Stealth Mode

More advanced than Selenium, better at bypassing:

```bash
# Install
pip3 install playwright playwright-stealth
playwright install chromium
```

Create `raptorsupplies_playwright.py`:
```python
#!/usr/bin/env python3
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
import time

def scrape_with_playwright():
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )

        page = context.new_page()
        stealth_sync(page)  # Apply stealth mode

        # Navigate
        page.goto('https://www.raptorsupplies.com/robots.txt')
        time.sleep(10)  # Wait for Cloudflare

        # Get content
        content = page.content()
        print(content)

        browser.close()

scrape_with_playwright()
```

### Solution 5: Puppeteer (Node.js) with Extra Plugins

If you prefer Node.js:

```bash
npm install puppeteer puppeteer-extra puppeteer-extra-plugin-stealth
```

Create `scraper.js`:
```javascript
const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');

puppeteer.use(StealthPlugin());

(async () => {
  const browser = await puppeteer.launch({ headless: false });
  const page = await browser.newPage();

  await page.goto('https://www.raptorsupplies.com/robots.txt');
  await page.waitForTimeout(10000); // Wait for Cloudflare

  const content = await page.content();
  console.log(content);

  await browser.close();
})();
```

### Solution 6: FlareSolverr (Cloudflare Solver Proxy)

Advanced solution using a proxy service:

```bash
# Run FlareSolverr in Docker
docker run -d \
  --name=flaresolverr \
  -p 8191:8191 \
  ghcr.io/flaresolverr/flaresolverr:latest

# Then use it in your Python script
import requests

response = requests.post(
    'http://localhost:8191/v1',
    json={
        'cmd': 'request.get',
        'url': 'https://www.raptorsupplies.com/sitemap.xml',
        'maxTimeout': 60000
    }
)

result = response.json()
if result['status'] == 'ok':
    content = result['solution']['response']
    print(content)
```

### Solution 7: Contact Raptor Supplies Directly

The most legitimate approach:

```
Email: sales@raptorsupplies.com or info@raptorsupplies.com
Phone: (Check their website)

Request:
- API access for bulk data
- Product catalog export
- B2B partnership
- Data feed service
```

Many B2B suppliers offer:
- EDI (Electronic Data Interchange)
- API endpoints for partners
- CSV/XML feeds
- FTP access for catalogs

## 🎯 Recommended Workflow

### For Quick Testing:
1. **Manual download** (Solution 1)
2. Parse locally with Python script

### For Production/Scale:
1. **ScraperAPI** (Solution 3A) - $49/month
2. Reliable, handles Cloudflare automatically
3. Simple API integration

### For Budget Projects:
1. **Octoparse** free tier (Solution 2B)
2. Manual extraction for small datasets
3. Browser extensions for one-time scrapes

### For Large Scale:
1. **Contact Raptor Supplies** (Solution 7)
2. Request official API access
3. Establish business partnership

## 📋 Quick Start: Manual Method

Since automation is challenging, here's the fastest way:

```bash
# 1. Open Chrome/Firefox
# 2. Visit: https://www.raptorsupplies.com/robots.txt
# 3. Find sitemap URLs (look for lines starting with "Sitemap:")
# 4. Visit each sitemap URL
# 5. Right-click > Save As > sitemap1.xml, sitemap2.xml, etc.

# 6. Parse saved files:
python3 << 'EOF'
import xml.etree.ElementTree as ET
import json
import glob

all_products = []

for file in glob.glob('sitemap*.xml'):
    tree = ET.parse(file)
    root = tree.getroot()

    ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

    for url in root.findall('.//s:loc', ns):
        if '/product' in url.text.lower():
            all_products.append(url.text)

with open('raptorsupplies_urls.json', 'w') as f:
    json.dump({'products': all_products}, f, indent=2)

print(f"✅ Found {len(all_products)} products!")
EOF
```

## 🚨 Important Notes

### Legal & Ethical:
- ✅ Check their Terms of Service
- ✅ Respect robots.txt rules
- ✅ Don't overload their servers
- ✅ Consider asking for permission/API access

### Technical:
- Cloudflare protection is **intentional**
- They don't want automated scraping
- Manual access is allowed
- Business partnerships may offer data feeds

### Best Practices:
1. Start with official channels (API, partnership)
2. Use paid services if automation needed
3. Respect rate limits
4. Identify your bot in User-Agent
5. Scrape during off-peak hours

## 📊 Cost Comparison

| Solution | Cost | Difficulty | Reliability | Scale |
|----------|------|------------|-------------|-------|
| Manual | Free | Easy | 100% | Small |
| Browser Extension | Free | Easy | 100% | Medium |
| ScraperAPI | $49/mo | Medium | 95% | Large |
| Bright Data | $500/mo | Medium | 99% | Very Large |
| FlareSolverr | Free | Hard | 70% | Medium |
| Official API | Varies | Easy | 100% | Unlimited |

## 🎓 Learning Resources

### Cloudflare Bypass:
- https://github.com/FlareSolverr/FlareSolverr
- https://github.com/ultrafunkamsterdam/undetected-chromedriver
- https://www.zenrows.com/blog/bypass-cloudflare

### Legal Scraping:
- https://www.scraperapi.com/blog/legal-web-scraping/
- https://tosdr.org/ (Terms of Service analyzer)

## 🛠️ Files Created

I've created these scrapers for you:

1. **raptorsupplies_scraper.py** - Basic HTTP scraper (blocked by Cloudflare)
2. **sitemaps_raptorsupplies_scraper.py** - Sitemap scraper (blocked)
3. **raptorsupplies_browser_scraper.py** - Browser automation (struggles with Cloudflare)
4. **raptorsupplies_config.yml** - Configuration file

All are functional but Cloudflare blocks them. Use solutions above instead.

## ❓ Next Steps

Choose based on your situation:

**Just need data once?**
→ Manual download + local parsing (Solution 1)

**Need recurring updates?**
→ ScraperAPI (Solution 3A)

**Building a product?**
→ Contact Raptor Supplies for API (Solution 7)

**Want to learn?**
→ Try Playwright/Puppeteer (Solutions 4 & 5)

## 💡 Pro Tip

Many industrial supply companies like Raptor Supplies offer:
- Bulk pricing catalogs
- Partner programs
- EDI integrations
- API access for verified businesses

**It's often easier (and legal) to partner with them than to scrape!**

---

Need help with any specific solution? Let me know! 🚀
