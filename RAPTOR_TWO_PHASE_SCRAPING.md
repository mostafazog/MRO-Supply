# Raptor Supplies Two-Phase Scraping System

## Overview

Raptor Supplies uses collection/family pages that contain multiple individual products. To scrape complete product details, we use a two-phase approach:

### Phase 1: Individual Product URL Extraction (Current)
Extract individual product URLs from collection pages

### Phase 2: Individual Product Scraping (Next)
Scrape full details from individual product pages

---

## Phase 1: URL Extraction

### Problem
The sitemaps contain ~89,000 collection page URLs like:
```
https://www.raptorsupplies.com/c/abrasives/p/3m-236u-hookit-clean-sanding-sheets
```

Each collection page contains 3-30 individual products, but doesn't show:
- Individual SKUs
- Individual prices
- Product specifications
- Stock availability

### Solution
Extract individual product URLs from each collection page using multiple strategies:

**Extraction Strategies:**
1. **Table Links** - Look for product links in variant tables
2. **Buy/View Buttons** - Extract URLs from action buttons
3. **Non-Category Links** - Filter links containing `/item/` or `/i/`
4. **Data Attributes** - Find elements with `data-sku`, `data-product-id`
5. **Structured Data** - Parse JSON-LD for product URLs

### Files

**Worker Script:** `raptorsupplies_url_extractor_worker.py`
- Processes collection pages assigned to this worker
- Extracts individual product URLs using multiple strategies
- Handles Cloudflare challenges
- Outputs JSON file with found URLs

**Aggregator:** `raptorsupplies_url_aggregator.py`
- Combines results from all workers
- Removes duplicates
- Creates final URL list

**GitHub Workflow:** `.github/workflows/extract-raptor-urls.yml`
- Distributes work across 10 parallel workers
- Runs in GitHub Actions environment (better Cloudflare bypass)
- Automatically aggregates results

### Running URL Extraction

**Test on 50 collections:**
```bash
gh workflow run extract-raptor-urls.yml \
  -f total_collections=50 \
  -f workers=5 \
  -f use_browser=true
```

**Full extraction (all 89K collections):**
```bash
gh workflow run extract-raptor-urls.yml \
  -f total_collections=89155 \
  -f workers=10 \
  -f use_browser=true
```

### Expected Output

**Collection pages:** 89,155
**Estimated individual products:** 300,000 - 500,000
(Assuming 3-8 products per collection on average)

**Output files:**
- `raptor_individual_products.json` - Full data with metadata
- `raptor_individual_products_urls.txt` - Plain text URL list
- `url_extraction_summary.json` - Statistics

---

## Phase 2: Individual Product Scraping (To Be Implemented)

### Goal
Scrape full product details from individual product URLs:
- Product name
- SKU / Part number
- Price
- Detailed specifications
- Images (high-res)
- Stock availability
- Manufacturer info
- Related products

### Implementation Plan

1. **Create Individual Product Scraper**
   - Load URLs from Phase 1 output
   - Extract all product details
   - Handle different product page templates

2. **Create GitHub Workflow**
   - Similar to Phase 1 but for product scraping
   - Distribute 300K+ URLs across workers
   - Aggregate final product data

3. **Run Full Scrape**
   - Process all individual products
   - Generate final database

### Timeline

- Phase 1 URL Extraction: ~1-2 hours for 89K collections
- Phase 2 Product Scraping: ~6-12 hours for 300K+ products
- Total: ~12-15 hours for complete database

---

## Current Status

✅ Phase 1 infrastructure complete
⏳ Phase 1 test running (50 collections)
⏳ Phase 2 implementation pending

---

## Advantages of Two-Phase Approach

1. **Separation of Concerns**
   - URL extraction is fast (no product parsing)
   - Product scraping can focus on data quality

2. **Resumability**
   - If Phase 2 fails, no need to re-extract URLs
   - Can process URLs in batches

3. **Flexibility**
   - Can scrape specific product categories
   - Can update products without re-discovering URLs

4. **Efficiency**
   - Phase 1: 3-5 seconds per collection
   - Phase 2: 5-10 seconds per product
   - Parallel execution on GitHub Actions

---

## Next Steps

1. Wait for Phase 1 test to complete
2. Verify individual URLs were found
3. Create Phase 2 scraper if URLs look good
4. Run full extraction + scraping pipeline
