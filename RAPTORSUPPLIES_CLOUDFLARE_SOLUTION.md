# Raptor Supplies - Cloudflare Protection Solution

## Problem
The website `raptorsupplies.com` is protected by **Cloudflare** with:
- JavaScript challenges
- Browser fingerprinting
- Anti-bot detection

All direct HTTP requests return **403 Forbidden**.

## Solution: Browser Automation

### Option 1: Selenium with Undetected ChromeDriver (Recommended)

This is the most reliable method for bypassing Cloudflare.

#### Installation
```bash
# Install required packages
pip3 install undetected-chromedriver selenium

# Make sure Chrome/Chromium is installed on your system
# Ubuntu/Debian:
sudo apt-get install chromium-browser

# Or use Google Chrome
```

#### Usage
```bash
# Run the browser-based scraper
python3 raptorsupplies_browser_scraper.py

# Show browser window (for debugging)
python3 raptorsupplies_browser_scraper.py --no-headless

# Custom output file
python3 raptorsupplies_browser_scraper.py --output my_urls.json
```

#### How It Works
1. Launches a real Chrome browser (headless or visible)
2. Uses undetected-chromedriver to bypass Cloudflare detection
3. Waits for JavaScript challenges to complete
4. Accesses robots.txt and sitemaps
5. Extracts all product URLs

### Option 2: Playwright (Alternative)

Playwright is another modern browser automation tool.

```bash
# Install
pip3 install playwright
playwright install chromium

# Create scraper using Playwright
# (similar approach to Selenium)
```

### Option 3: Puppeteer (Node.js)

If you prefer Node.js:

```bash
npm install puppeteer puppeteer-extra puppeteer-extra-plugin-stealth
```

### Option 4: Paid Services

If automation doesn't work, consider:

1. **ScraperAPI** - https://www.scraperapi.com/
   - Handles Cloudflare automatically
   - Pay per request
   - Very reliable

2. **Bright Data** - https://brightdata.com/
   - Premium proxy service
   - Includes Cloudflare bypass

3. **Zyte (Scrapy Cloud)** - https://www.zyte.com/
   - Managed scraping infrastructure

## Scraping Strategy

Once you bypass Cloudflare and get product URLs:

### 1. Extract URLs from Sitemap
```bash
python3 raptorsupplies_browser_scraper.py
# Outputs: raptorsupplies_urls.json
```

### 2. Scrape Products from URLs
```python
# Load URLs
with open('raptorsupplies_urls.json', 'r') as f:
    data = json.load(f)
    product_urls = data['product_urls']

# Scrape each product using browser automation
for url in product_urls:
    driver.get(url)
    # Wait for Cloudflare
    # Extract product data
```

### 3. Rate Limiting
Even with browser automation, be respectful:
- 5-10 second delays between requests
- Rotate user agents
- Restart browser every 50 products
- Use residential proxies if needed

## Manual Alternative

If automation fails, you can:

1. **Manual Download**
   - Open browser manually
   - Visit: https://www.raptorsupplies.com/sitemap.xml
   - Save the XML file
   - Parse it locally

2. **Browser Extensions**
   - Use extensions like "Web Scraper" for Chrome
   - Visual scraping without code

3. **API Access**
   - Contact Raptor Supplies for API access
   - Many B2B suppliers offer APIs for partners

## Testing Cloudflare Bypass

Test if your solution works:

```bash
# Run the browser scraper
python3 raptorsupplies_browser_scraper.py --no-headless

# Watch the browser window:
# - Should show "Just a moment..." briefly
# - Then load the actual page content
# - If it works, you'll see product URLs extracted
```

## Troubleshooting

### Error: "Chrome not found"
```bash
# Install Chrome/Chromium
sudo apt-get install chromium-browser

# Or download Chrome:
# https://www.google.com/chrome/
```

### Error: "undetected-chromedriver" issues
```bash
# Update to latest version
pip3 install --upgrade undetected-chromedriver

# Clear cache
pip3 cache purge
```

### Cloudflare Still Blocking
- Use residential proxies
- Increase wait times
- Try different user agents
- Use headful mode (not headless)

### Browser Keeps Crashing
```bash
# Increase memory
# Add these Chrome options:
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--no-sandbox')
```

## Legal & Ethical Considerations

⚠️ **Important:**

1. **Check robots.txt** - Respect crawl rules
2. **Terms of Service** - Review site's ToS
3. **Rate Limiting** - Don't overload their servers
4. **Data Usage** - Only for legitimate purposes
5. **API First** - Ask for official API access if available

## Best Practices

1. **Start Small**
   - Test with 10-20 products first
   - Verify data quality
   - Then scale up

2. **Monitor Success Rate**
   - Track how many products successfully scraped
   - Adjust delays if needed

3. **Handle Failures**
   - Save checkpoint frequently
   - Retry failed products
   - Log errors for analysis

4. **Be a Good Bot**
   - Identify yourself in User-Agent
   - Respect crawl delays
   - Scrape during off-peak hours

## Example Complete Workflow

```bash
# 1. Install dependencies
pip3 install undetected-chromedriver selenium

# 2. Get product URLs from sitemap
python3 raptorsupplies_browser_scraper.py

# 3. Check results
cat raptorsupplies_urls.json | python3 -m json.tool | head -30

# 4. Create product scraper (use the URLs you extracted)
# python3 raptorsupplies_product_scraper.py --url-file raptorsupplies_urls.json

# 5. Monitor progress
tail -f ./logs/raptorsupplies_browser.log
```

## Need Help?

If you're still stuck:
1. Check browser console for errors
2. Try with `--no-headless` to see what's happening
3. Use ScraperAPI or similar service as fallback
4. Consider contacting Raptor Supplies for data partnership

Good luck! 🚀
