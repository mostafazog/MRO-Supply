# Raptor Supplies Scraper - Usage Guide

## Overview
This scraper is designed to extract product data from raptorsupplies.com with advanced anti-ban protection.

## Features
- ✅ Anti-ban protection with user agent rotation
- ✅ Intelligent rate limiting
- ✅ Session management
- ✅ Retry logic with exponential backoff
- ✅ Checkpoint system (resume scraping)
- ✅ Detailed logging and statistics
- ✅ 403 error handling

## Quick Start

### 1. Install Dependencies
```bash
pip3 install requests beautifulsoup4 pyyaml
```

### 2. Test with Small Range
First, test with a small range to understand the site structure:
```bash
python3 raptorsupplies_scraper.py --start 1 --end 10
```

### 3. Analyze Results
Check the output in:
- `./data/raptorsupplies/results/` - Individual product JSON files
- `./logs/raptorsupplies_scraper.log` - Detailed log
- `raptorsupplies_checkpoint.json` - Progress checkpoint

### 4. Adjust Configuration
Based on test results, you may need to:
1. **Update product URL pattern** in `raptorsupplies_config.yml`
2. **Adjust HTML selectors** in `raptorsupplies_scraper.py` (`_parse_product` method)
3. **Fine-tune rate limiting** if you get too many 403 errors

## Configuration

### Important Settings in `raptorsupplies_config.yml`

```yaml
source:
  # Adjust this URL pattern based on actual site structure
  product_url_pattern: "https://www.raptorsupplies.com/products/{product_id}"

rate_limiting:
  products_per_minute: 6  # Very conservative - increase if stable
  min_delay_seconds: 5    # Minimum delay between requests
  max_delay_seconds: 15   # Maximum delay
```

## Usage Examples

### Basic Scraping
```bash
# Scrape products 1-100
python3 raptorsupplies_scraper.py --start 1 --end 100

# Scrape products 1000-2000
python3 raptorsupplies_scraper.py --start 1000 --end 2000
```

### Custom Output
```bash
# Save to custom file
python3 raptorsupplies_scraper.py --start 1 --end 100 --output my_products.json
```

### Resume from Checkpoint
The scraper automatically resumes from the last checkpoint:
```bash
# Just run again - it will resume from where it left off
python3 raptorsupplies_scraper.py --start 1 --end 10000
```

## Customizing HTML Parsing

You'll likely need to adjust the HTML selectors in the `_parse_product()` method. Here's how:

### 1. Inspect a Product Page
```bash
# Download a sample page
curl "https://www.raptorsupplies.com/products/SOME-PRODUCT" > sample.html
```

### 2. Identify Selectors
Look at `sample.html` and identify the CSS selectors for:
- Product name (h1, .product-title, etc.)
- Price (.price, .product-price, etc.)
- Description (.description, etc.)
- Images (.product-images img, etc.)
- SKU, brand, category, etc.

### 3. Update Selectors
Edit `raptorsupplies_scraper.py` around line 280 in the `_parse_product()` method:
```python
name_selectors = [
    'h1.your-actual-selector',  # Add real selectors here
    'h1.product-title',
    # ... more options
]
```

## Dealing with 403 Errors

If you get many 403 Forbidden errors:

### 1. Slow Down
```yaml
rate_limiting:
  products_per_minute: 3  # Reduce from 6 to 3
  min_delay_seconds: 10   # Increase from 5 to 10
```

### 2. Longer Cooldowns
```yaml
ban_detection:
  cooldown_period: 1800  # Increase from 900 to 1800 (30 min)
```

### 3. Use Proxies (Advanced)
Consider using residential proxies like:
- WebShare.io
- BrightData
- Smartproxy

## Monitoring Progress

### Check Logs
```bash
tail -f ./logs/raptorsupplies_scraper.log
```

### View Statistics
Statistics are printed at the end and periodically during scraping:
- Total requests
- Success rate
- HTTP status codes (200, 403, 404)
- Bans detected

### Check Results
```bash
# Count scraped products
ls -1 ./data/raptorsupplies/results/ | wc -l

# View a sample product
cat ./data/raptorsupplies/results/product_1.json | python3 -m json.tool
```

## Output Format

Each product is saved as a JSON file:
```json
{
  "product_id": 12345,
  "url": "https://www.raptorsupplies.com/products/12345",
  "name": "Product Name",
  "price": 29.99,
  "description": "Full product description...",
  "images": ["image1.jpg", "image2.jpg"],
  "main_image": "image1.jpg",
  "sku": "SKU-12345",
  "brand": "Brand Name",
  "availability": "In Stock",
  "category": "Category > Subcategory",
  "scraped_at": "2025-12-26T10:30:00"
}
```

## Troubleshooting

### Problem: All products return 404
**Solution**: The product ID pattern might be wrong. Check actual product URLs on the site.

### Problem: Too many 403 errors
**Solution**: Reduce scraping speed, increase delays, add more user agents, or use proxies.

### Problem: No data extracted
**Solution**: HTML selectors need adjustment. Inspect the actual HTML and update selectors.

### Problem: Scraper seems stuck
**Solution**: Check if you're in a cooldown period (check logs for "cooling down" messages).

## Best Practices

1. **Start small**: Always test with 10-50 products first
2. **Be respectful**: Don't hammer the server - use reasonable delays
3. **Monitor logs**: Watch for patterns in errors
4. **Save checkpoints**: The scraper auto-saves, so you can stop/resume anytime
5. **Adjust selectors**: Every site is different - customize the parsing logic

## Advanced: Distributed Scraping

For large-scale scraping, consider:
1. Multiple machines with different IPs
2. Residential proxy rotation
3. Cloud functions (AWS Lambda, Azure Functions)
4. GitHub Actions (like in your MRO Supply scraper)

## Support

If you need help:
1. Check logs in `./logs/raptorsupplies_scraper.log`
2. Review error files in `./data/raptorsupplies/errors/`
3. Inspect checkpoint: `cat raptorsupplies_checkpoint.json`

## Example Workflow

```bash
# 1. Test with 10 products
python3 raptorsupplies_scraper.py --start 1 --end 10

# 2. Check if data looks good
cat ./data/raptorsupplies/results/product_1.json

# 3. If good, run larger batch
python3 raptorsupplies_scraper.py --start 1 --end 1000

# 4. Monitor progress
tail -f ./logs/raptorsupplies_scraper.log

# 5. If interrupted, just run again to resume
python3 raptorsupplies_scraper.py --start 1 --end 1000
```

Good luck with your scraping! 🚀
