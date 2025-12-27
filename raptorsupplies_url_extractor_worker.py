"""
Raptor Supplies Individual Product URL Extractor - GitHub Worker
Extracts individual product URLs from collection pages
"""

import json
import time
import random
import os
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import undetected_chromedriver as uc
from datetime import datetime

# Environment variables from GitHub Actions
WORKER_ID = int(os.getenv('WORKER_ID', 0))
TOTAL_WORKERS = int(os.getenv('TOTAL_WORKERS', 1))
TOTAL_COLLECTIONS = int(os.getenv('TOTAL_COLLECTIONS', 100))
USE_BROWSER = os.getenv('USE_BROWSER', 'true').lower() == 'true'


class IndividualProductExtractor:
    def __init__(self, worker_id, total_workers, total_collections):
        self.worker_id = worker_id
        self.total_workers = total_workers
        self.total_collections = total_collections
        self.driver = None
        self.collection_urls = []
        self.individual_urls = set()
        self.errors = []

    def init_browser(self):
        """Initialize undetected Chrome browser"""
        print(f"🚀 Worker {self.worker_id}: Initializing browser...")
        options = uc.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')

        self.driver = uc.Chrome(options=options)
        print(f"✅ Worker {self.worker_id}: Browser initialized")

    def load_collection_urls(self):
        """Load and distribute collection URLs among workers"""
        print(f"📁 Worker {self.worker_id}: Loading collection URLs...")

        with open('raptorsupplies_urls.json', 'r') as f:
            data = json.load(f)
            all_urls = data.get('product_urls', [])[:self.total_collections]

        # Distribute URLs among workers
        self.collection_urls = [url for i, url in enumerate(all_urls) if i % self.total_workers == self.worker_id]

        print(f"✅ Worker {self.worker_id}: Assigned {len(self.collection_urls)} collection URLs")

    def wait_for_cloudflare(self, timeout=30):
        """Wait for Cloudflare challenge to complete"""
        try:
            # Check if Cloudflare challenge is present
            if "Just a moment" in self.driver.page_source or "Checking your browser" in self.driver.page_source:
                print(f"   ⏳ Worker {self.worker_id}: Waiting for Cloudflare...")
                time.sleep(10)  # Give Cloudflare time to resolve
            return True
        except:
            return True

    def extract_individual_urls(self, collection_url):
        """Extract individual product URLs from a collection page"""
        try:
            print(f"\n   📄 Worker {self.worker_id}: Processing {collection_url}")

            self.driver.get(collection_url)
            time.sleep(3)  # Initial page load

            self.wait_for_cloudflare()

            # Wait for content to load
            time.sleep(2)

            found_urls = set()

            # Strategy 1: Look for product links in tables (common for variant listings)
            try:
                table_links = self.driver.find_elements(By.CSS_SELECTOR, "table a[href*='/item/'], table a[href*='/i/']")
                for link in table_links:
                    href = link.get_attribute('href')
                    if href and '/item/' in href or '/i/' in href:
                        found_urls.add(href)
                        print(f"      ✓ Found: {href}")
            except Exception as e:
                pass

            # Strategy 2: Look for buy/view buttons with product URLs
            try:
                product_buttons = self.driver.find_elements(By.CSS_SELECTOR,
                    "a[href*='/item/'], a[href*='/i/'], a.btn[href*='raptor'], button[data-url*='/item/']")
                for button in product_buttons:
                    href = button.get_attribute('href') or button.get_attribute('data-url')
                    if href and (('/item/' in href) or ('/i/' in href)):
                        found_urls.add(href)
                        print(f"      ✓ Found: {href}")
            except Exception as e:
                pass

            # Strategy 3: Look for links that are NOT category links
            try:
                all_links = self.driver.find_elements(By.TAG_NAME, 'a')
                for link in all_links:
                    href = link.get_attribute('href')
                    if href and 'raptorsupplies.com' in href:
                        # Exclude category, collection, brand pages
                        if not any(exclude in href for exclude in ['/c/', '/b/', '/brand/', '/category/', '/p/']):
                            # Include if it looks like a product page
                            if any(include in href for include in ['/item/', '/i/', '/product/', '/sku/']):
                                found_urls.add(href)
                                print(f"      ✓ Found: {href}")
            except Exception as e:
                pass

            # Strategy 4: Look for data attributes with SKUs or product IDs
            try:
                elements_with_sku = self.driver.find_elements(By.CSS_SELECTOR,
                    "[data-sku], [data-product-id], [data-item-id]")
                for elem in elements_with_sku:
                    # Try to find associated link
                    try:
                        link = elem.find_element(By.TAG_NAME, 'a')
                        href = link.get_attribute('href')
                        if href:
                            found_urls.add(href)
                            print(f"      ✓ Found: {href}")
                    except:
                        pass
            except Exception as e:
                pass

            # Strategy 5: Look for structured data (JSON-LD)
            try:
                scripts = self.driver.find_elements(By.CSS_SELECTOR, "script[type='application/ld+json']")
                for script in scripts:
                    content = script.get_attribute('innerHTML')
                    if content:
                        # Look for URLs in JSON
                        import re
                        urls = re.findall(r'https://www\.raptorsupplies\.com/[^"]+', content)
                        for url in urls:
                            if '/item/' in url or '/i/' in url:
                                found_urls.add(url)
                                print(f"      ✓ Found in JSON-LD: {url}")
            except Exception as e:
                pass

            if found_urls:
                print(f"   ✅ Worker {self.worker_id}: Found {len(found_urls)} individual product URLs")
            else:
                print(f"   ⚠️  Worker {self.worker_id}: No individual products found (might be a product family page)")

            # Rate limiting
            time.sleep(random.uniform(3, 6))

            return list(found_urls)

        except Exception as e:
            error_msg = f"Error processing {collection_url}: {str(e)}"
            print(f"   ❌ Worker {self.worker_id}: {error_msg}")
            self.errors.append({
                "url": collection_url,
                "error": error_msg,
                "timestamp": datetime.now().isoformat()
            })
            return []

    def run(self):
        """Run the extraction process"""
        print("=" * 80)
        print(f"🔍 WORKER {self.worker_id} - INDIVIDUAL PRODUCT URL EXTRACTOR")
        print("=" * 80)

        # Load collection URLs
        self.load_collection_urls()

        if not self.collection_urls:
            print(f"⚠️  Worker {self.worker_id}: No URLs assigned, exiting...")
            return

        # Initialize browser
        if USE_BROWSER:
            self.init_browser()

        # Process each collection
        print(f"\n🔄 Worker {self.worker_id}: Extracting individual product URLs...")

        for i, collection_url in enumerate(self.collection_urls, 1):
            print(f"\n[Worker {self.worker_id}] [{i}/{len(self.collection_urls)}]")

            urls = self.extract_individual_urls(collection_url)
            self.individual_urls.update(urls)

        # Save results
        output_file = f"worker_{self.worker_id}_individual_urls.json"
        error_file = f"worker_{self.worker_id}_extraction_errors.json"

        print(f"\n💾 Worker {self.worker_id}: Saving results to {output_file}...")

        with open(output_file, 'w') as f:
            json.dump({
                "worker_id": self.worker_id,
                "extracted_at": datetime.now().isoformat(),
                "collections_processed": len(self.collection_urls),
                "individual_urls_found": len(self.individual_urls),
                "urls": sorted(list(self.individual_urls))
            }, f, indent=2)

        # Save errors
        if self.errors:
            with open(error_file, 'w') as f:
                json.dump(self.errors, f, indent=2)

        # Summary
        print("\n" + "=" * 80)
        print(f"✨ WORKER {self.worker_id} COMPLETE!")
        print("=" * 80)
        print(f"📊 Collections processed: {len(self.collection_urls)}")
        print(f"🎯 Individual URLs found: {len(self.individual_urls)}")
        print(f"❌ Errors: {len(self.errors)}")

        # Cleanup
        if self.driver:
            self.driver.quit()


if __name__ == "__main__":
    extractor = IndividualProductExtractor(WORKER_ID, TOTAL_WORKERS, TOTAL_COLLECTIONS)
    extractor.run()
