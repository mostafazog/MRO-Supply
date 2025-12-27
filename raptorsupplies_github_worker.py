#!/usr/bin/env python3
"""
Raptor Supplies GitHub Actions Worker
Scrapes assigned batch of products in distributed manner
"""

import json
import time
import os
import sys
import random
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

# Check if browser mode enabled
USE_BROWSER = os.getenv('USE_BROWSER', 'true').lower() == 'true'

if USE_BROWSER:
    try:
        import undetected_chromedriver as uc
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from bs4 import BeautifulSoup
    except ImportError:
        print("⚠️ Browser mode requested but dependencies not installed")
        USE_BROWSER = False

if not USE_BROWSER:
    import requests
    from bs4 import BeautifulSoup


class RaptorSuppliesWorker:
    """Worker that scrapes assigned products"""

    def __init__(self, worker_id: int, total_workers: int, total_products: int, start_index: int = 0):
        self.worker_id = worker_id
        self.total_workers = total_workers
        self.total_products = total_products
        self.start_index = start_index

        self.use_browser = USE_BROWSER
        self.driver = None

        # Load product URLs
        self.product_urls = self._load_urls()

        # Calculate this worker's batch
        self.my_urls = self._assign_batch()

        self.results = []
        self.errors = []

        print(f"🤖 Worker {worker_id} initialized")
        print(f"   Total URLs available: {len(self.product_urls):,}")
        print(f"   My batch size: {len(self.my_urls):,}")
        print(f"   Mode: {'Browser' if self.use_browser else 'HTTP'}")

    def _load_urls(self) -> List[str]:
        """Load product URLs from JSON file"""
        url_file = 'raptorsupplies_urls.json'

        if not os.path.exists(url_file):
            print(f"❌ URL file not found: {url_file}")
            return []

        with open(url_file, 'r') as f:
            data = json.load(f)
            urls = data.get('product_urls', [])
            print(f"📋 Loaded {len(urls):,} URLs from {url_file}")
            return urls

    def _assign_batch(self) -> List[str]:
        """Assign batch of URLs to this worker"""
        # Take first N products
        urls_to_process = self.product_urls[self.start_index:self.start_index + self.total_products]

        # Distribute among workers
        my_urls = []
        for i, url in enumerate(urls_to_process):
            if i % self.total_workers == self.worker_id:
                my_urls.append(url)

        return my_urls

    def init_browser(self):
        """Initialize browser for Cloudflare bypass"""
        if not self.use_browser:
            return

        try:
            print("🌐 Initializing browser...")
            options = Options()
            options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')

            # Try to use system Chrome
            options.binary_location = '/usr/bin/chromium-browser'

            self.driver = uc.Chrome(options=options)
            print("✅ Browser initialized")

        except Exception as e:
            print(f"⚠️ Browser initialization failed: {e}")
            print("   Falling back to HTTP mode")
            self.use_browser = False
            self.driver = None

    def wait_for_cloudflare(self, timeout: int = 30) -> bool:
        """Wait for Cloudflare challenge to complete"""
        if not self.driver:
            return False

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                page_source = self.driver.page_source.lower()

                if 'just a moment' in page_source or 'checking your browser' in page_source:
                    time.sleep(2)
                    continue

                if 'cloudflare' not in page_source or len(page_source) > 10000:
                    return True

                time.sleep(2)

            except Exception as e:
                print(f"   Error waiting for Cloudflare: {e}")
                time.sleep(2)

        return False

    def scrape_product_browser(self, url: str) -> Optional[Dict]:
        """Scrape product using browser automation"""
        try:
            self.driver.get(url)

            # Wait for Cloudflare
            if not self.wait_for_cloudflare():
                return None

            # Additional wait for page load
            time.sleep(3)

            # Parse page
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            return self._parse_product(soup, url)

        except Exception as e:
            print(f"   ❌ Error: {e}")
            return None

    def scrape_product_http(self, url: str) -> Optional[Dict]:
        """Scrape product using HTTP (likely to be blocked by Cloudflare)"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code == 403:
                print(f"   ⚠️ 403 Forbidden (Cloudflare blocking)")
                return None

            if response.status_code != 200:
                print(f"   ⚠️ HTTP {response.status_code}")
                return None

            soup = BeautifulSoup(response.text, 'html.parser')
            return self._parse_product(soup, url)

        except Exception as e:
            print(f"   ❌ Error: {e}")
            return None

    def _parse_product(self, soup: BeautifulSoup, url: str) -> Optional[Dict]:
        """Parse product data from HTML"""
        product = {
            'url': url,
            'scraped_at': datetime.now().isoformat(),
            'worker_id': self.worker_id
        }

        try:
            # Extract product name (adjust selectors based on actual HTML)
            name_selectors = ['h1.product-title', 'h1.product-name', 'h1[itemprop="name"]', 'h1']
            for selector in name_selectors:
                elem = soup.select_one(selector)
                if elem:
                    product['name'] = elem.get_text(strip=True)
                    break

            # Extract price
            price_selectors = ['.product-price', '[itemprop="price"]', '.price', 'span.money']
            for selector in price_selectors:
                elem = soup.select_one(selector)
                if elem:
                    product['price_text'] = elem.get_text(strip=True)
                    break

            # Extract SKU
            sku_selectors = ['[itemprop="sku"]', '.product-sku', '.sku']
            for selector in sku_selectors:
                elem = soup.select_one(selector)
                if elem:
                    product['sku'] = elem.get_text(strip=True)
                    break

            # Extract description
            desc_selectors = ['.product-description', '[itemprop="description"]', '.description']
            for selector in desc_selectors:
                elem = soup.select_one(selector)
                if elem:
                    desc = elem.get_text(strip=True)
                    product['description'] = desc[:500] if len(desc) > 500 else desc
                    break

            # Extract images
            images = []
            for img in soup.select('img[src*="product"], .product-image img'):
                src = img.get('src') or img.get('data-src')
                if src:
                    images.append(src)

            if images:
                product['images'] = images[:5]  # Max 5 images

            # Extract brand
            brand_selectors = ['[itemprop="brand"]', '.brand', '.manufacturer']
            for selector in brand_selectors:
                elem = soup.select_one(selector)
                if elem:
                    product['brand'] = elem.get_text(strip=True)
                    break

            # Must have at least a name
            if 'name' not in product:
                return None

            return product

        except Exception as e:
            print(f"   Parse error: {e}")
            return None

    def scrape_batch(self):
        """Scrape assigned batch of products"""
        print(f"\n{'='*70}")
        print(f"🚀 WORKER {self.worker_id} STARTING")
        print(f"{'='*70}")
        print(f"Products to scrape: {len(self.my_urls):,}")
        print(f"Mode: {'Browser (Cloudflare bypass)' if self.use_browser else 'HTTP'}")
        print()

        # Initialize browser if needed
        if self.use_browser:
            self.init_browser()

        # Scrape each product
        for i, url in enumerate(self.my_urls, 1):
            print(f"[{i}/{len(self.my_urls)}] {url}")

            # Scrape
            if self.use_browser and self.driver:
                product = self.scrape_product_browser(url)
            else:
                product = self.scrape_product_http(url)

            if product:
                self.results.append(product)
                print(f"   ✅ {product.get('name', 'Unknown')[:60]}")
            else:
                self.errors.append({
                    'url': url,
                    'timestamp': datetime.now().isoformat()
                })
                print(f"   ❌ Failed")

            # Rate limiting
            delay = random.uniform(5, 10) if self.use_browser else random.uniform(2, 5)
            if i < len(self.my_urls):  # Don't wait after last product
                print(f"   ⏳ Waiting {delay:.1f}s...")
                time.sleep(delay)

            # Progress update
            if i % 10 == 0:
                success_rate = (len(self.results) / i) * 100
                print(f"\n   📊 Progress: {i}/{len(self.my_urls)} | Success: {len(self.results)} ({success_rate:.1f}%)\n")

        # Cleanup
        if self.driver:
            self.driver.quit()

        # Save results
        self.save_results()

    def save_results(self):
        """Save results to JSON files"""
        # Save products
        products_file = f'worker_{self.worker_id}_products.json'
        with open(products_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        # Save errors
        errors_file = f'worker_{self.worker_id}_errors.json'
        with open(errors_file, 'w') as f:
            json.dump(self.errors, f, indent=2)

        # Summary
        print(f"\n{'='*70}")
        print(f"✅ WORKER {self.worker_id} COMPLETE")
        print(f"{'='*70}")
        print(f"Products scraped: {len(self.results):,}")
        print(f"Failed: {len(self.errors):,}")
        print(f"Success rate: {(len(self.results) / max(len(self.my_urls), 1)) * 100:.1f}%")
        print(f"\nSaved to:")
        print(f"  - {products_file}")
        print(f"  - {errors_file}")
        print(f"{'='*70}\n")


def main():
    """Main entry point"""
    # Get environment variables
    worker_id = int(os.getenv('WORKER_ID', 0))
    total_workers = int(os.getenv('TOTAL_WORKERS', 10))
    total_products = int(os.getenv('TOTAL_PRODUCTS', 1000))
    start_index = int(os.getenv('START_INDEX', 0))

    print(f"🤖 GitHub Actions Worker - Raptor Supplies")
    print(f"   Worker ID: {worker_id}")
    print(f"   Total Workers: {total_workers}")
    print(f"   Total Products: {total_products}")
    print(f"   Start Index: {start_index}")
    print()

    # Create worker
    worker = RaptorSuppliesWorker(
        worker_id=worker_id,
        total_workers=total_workers,
        total_products=total_products,
        start_index=start_index
    )

    # Run scraping
    try:
        worker.scrape_batch()
        return 0
    except KeyboardInterrupt:
        print("\n⏸️ Interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
