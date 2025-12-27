"""
Raptor Supplies Variant Scraper
Extracts individual product variants from collection pages
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
TOTAL_PRODUCTS = int(os.getenv('TOTAL_PRODUCTS', 100))
USE_BROWSER = os.getenv('USE_BROWSER', 'true').lower() == 'true'


class VariantScraper:
    def __init__(self, worker_id, total_workers, total_products):
        self.worker_id = worker_id
        self.total_workers = total_workers
        self.total_products = total_products
        self.driver = None
        self.collection_urls = []
        self.products = []
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
            all_urls = data.get('product_urls', [])[:self.total_products]

        # Distribute URLs among workers
        self.collection_urls = [url for i, url in enumerate(all_urls) if i % self.total_workers == self.worker_id]

        print(f"✅ Worker {self.worker_id}: Assigned {len(self.collection_urls)} collection URLs")

    def wait_for_cloudflare(self, timeout=30):
        """Wait for Cloudflare challenge to complete"""
        try:
            if "Just a moment" in self.driver.page_source or "Checking your browser" in self.driver.page_source:
                print(f"   ⏳ Worker {self.worker_id}: Waiting for Cloudflare...")
                time.sleep(10)
            return True
        except:
            return True

    def extract_variants(self, collection_url):
        """Extract all product variants from a collection page"""
        try:
            print(f"\n   📄 Worker {self.worker_id}: Processing {collection_url}")

            self.driver.get(collection_url)
            time.sleep(3)

            self.wait_for_cloudflare()
            time.sleep(2)

            # Extract collection-level info
            collection_name = ""
            collection_image = ""

            try:
                collection_name = self.driver.find_element(By.CSS_SELECTOR, "h1, .page-title, .product-name").text.strip()
            except:
                pass

            try:
                collection_image = self.driver.find_element(By.CSS_SELECTOR, "img.product-image, .gallery-image img, .main-image").get_attribute('src')
            except:
                pass

            # Strategy 1: Look for product table/grid with variants
            variants = []

            # Try table-based variant listing
            try:
                rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr, .product-table tr, .variant-list tr")
                print(f"      Found {len(rows)} table rows")

                for row in rows:
                    variant = self.parse_table_row(row, collection_url)
                    if variant:
                        variants.append(variant)
            except Exception as e:
                print(f"      Table parsing: {str(e)[:50]}")

            # Strategy 2: Look for card-based variants
            try:
                cards = self.driver.find_elements(By.CSS_SELECTOR, ".product-item, .variant-card, .product-card")
                print(f"      Found {len(cards)} product cards")

                for card in cards:
                    variant = self.parse_variant_card(card, collection_url)
                    if variant:
                        variants.append(variant)
            except Exception as e:
                print(f"      Card parsing: {str(e)[:50]}")

            # Strategy 3: Look for option/variant selectors
            try:
                options = self.driver.find_elements(By.CSS_SELECTOR, ".variant-option, .product-option, [data-variant]")
                print(f"      Found {len(options)} variant options")

                for option in options:
                    variant = self.parse_variant_option(option, collection_url)
                    if variant:
                        variants.append(variant)
            except Exception as e:
                print(f"      Option parsing: {str(e)[:50]}")

            # If no variants found, create one entry for the collection
            if not variants:
                print(f"      No variants found, using collection data")
                variants.append({
                    "url": collection_url,
                    "collection_name": collection_name or "Unknown",
                    "name": collection_name or "Unknown",
                    "sku": None,
                    "price": None,
                    "price_text": None,
                    "image": collection_image,
                    "specifications": {},
                    "in_stock": None,
                    "scraped_at": datetime.now().isoformat(),
                    "worker_id": self.worker_id
                })
            else:
                # Add collection info to variants
                for variant in variants:
                    variant["collection_url"] = collection_url
                    variant["collection_name"] = collection_name
                    if not variant.get("image") and collection_image:
                        variant["image"] = collection_image
                    variant["scraped_at"] = datetime.now().isoformat()
                    variant["worker_id"] = self.worker_id

            print(f"   ✅ Worker {self.worker_id}: Extracted {len(variants)} variants")

            # Rate limiting
            time.sleep(random.uniform(3, 6))

            return variants

        except Exception as e:
            error_msg = f"Error processing {collection_url}: {str(e)}"
            print(f"   ❌ Worker {self.worker_id}: {error_msg}")
            self.errors.append({
                "url": collection_url,
                "error": error_msg,
                "timestamp": datetime.now().isoformat()
            })
            return []

    def parse_table_row(self, row, base_url):
        """Parse a table row for variant data"""
        try:
            variant = {"url": base_url}

            # Look for SKU
            try:
                sku_elem = row.find_element(By.CSS_SELECTOR, ".sku, [data-sku], .part-number, .model")
                variant["sku"] = sku_elem.text.strip()
            except:
                variant["sku"] = None

            # Look for product name
            try:
                name_elem = row.find_element(By.CSS_SELECTOR, ".product-name, .title, .name, a")
                variant["name"] = name_elem.text.strip()

                # Try to get product-specific URL
                try:
                    url = name_elem.get_attribute('href')
                    if url:
                        variant["url"] = url
                except:
                    pass
            except:
                variant["name"] = None

            # Look for price
            try:
                price_elem = row.find_element(By.CSS_SELECTOR, ".price, [data-price], .cost")
                variant["price_text"] = price_elem.text.strip()

                # Try to extract numeric price
                import re
                price_match = re.search(r'[\$]?\s*(\d+[\d,]*\.?\d*)', variant["price_text"])
                if price_match:
                    variant["price"] = float(price_match.group(1).replace(',', ''))
                else:
                    variant["price"] = None
            except:
                variant["price"] = None
                variant["price_text"] = None

            # Look for stock status
            try:
                stock_elem = row.find_element(By.CSS_SELECTOR, ".stock, .availability, [data-stock]")
                stock_text = stock_elem.text.strip().lower()
                variant["in_stock"] = "in stock" in stock_text or "available" in stock_text
            except:
                variant["in_stock"] = None

            # Extract all cells as potential specs
            try:
                cells = row.find_elements(By.TAG_NAME, "td")
                variant["specifications"] = {}
                for i, cell in enumerate(cells):
                    text = cell.text.strip()
                    if text and text not in [variant.get("name"), variant.get("sku"), variant.get("price_text")]:
                        variant["specifications"][f"spec_{i}"] = text
            except:
                variant["specifications"] = {}

            # Look for image
            try:
                img = row.find_element(By.TAG_NAME, "img")
                variant["image"] = img.get_attribute('src')
            except:
                variant["image"] = None

            # Only return if we have at least a name or SKU
            if variant.get("name") or variant.get("sku"):
                return variant
            return None

        except Exception as e:
            return None

    def parse_variant_card(self, card, base_url):
        """Parse a variant card for product data"""
        try:
            variant = {"url": base_url}

            # Similar parsing logic as table row
            try:
                variant["name"] = card.find_element(By.CSS_SELECTOR, ".product-name, .title, h3, h4, a").text.strip()
            except:
                variant["name"] = None

            try:
                variant["sku"] = card.find_element(By.CSS_SELECTOR, ".sku, [data-sku]").text.strip()
            except:
                variant["sku"] = None

            try:
                price_elem = card.find_element(By.CSS_SELECTOR, ".price, [data-price]")
                variant["price_text"] = price_elem.text.strip()

                import re
                price_match = re.search(r'[\$]?\s*(\d+[\d,]*\.?\d*)', variant["price_text"])
                if price_match:
                    variant["price"] = float(price_match.group(1).replace(',', ''))
                else:
                    variant["price"] = None
            except:
                variant["price"] = None
                variant["price_text"] = None

            try:
                img = card.find_element(By.TAG_NAME, "img")
                variant["image"] = img.get_attribute('src')
            except:
                variant["image"] = None

            variant["specifications"] = {}

            if variant.get("name") or variant.get("sku"):
                return variant
            return None

        except Exception as e:
            return None

    def parse_variant_option(self, option, base_url):
        """Parse a variant option/selector"""
        try:
            variant = {"url": base_url}

            variant["name"] = option.get_attribute('data-name') or option.text.strip()
            variant["sku"] = option.get_attribute('data-sku')

            price_attr = option.get_attribute('data-price')
            if price_attr:
                try:
                    variant["price"] = float(price_attr)
                    variant["price_text"] = f"${price_attr}"
                except:
                    variant["price"] = None
                    variant["price_text"] = None
            else:
                variant["price"] = None
                variant["price_text"] = None

            variant["image"] = option.get_attribute('data-image')
            variant["specifications"] = {}

            if variant.get("name") or variant.get("sku"):
                return variant
            return None

        except Exception as e:
            return None

    def run(self):
        """Run the scraping process"""
        print("=" * 80)
        print(f"🔍 WORKER {self.worker_id} - VARIANT SCRAPER")
        print("=" * 80)

        self.load_collection_urls()

        if not self.collection_urls:
            print(f"⚠️  Worker {self.worker_id}: No URLs assigned, exiting...")
            return

        if USE_BROWSER:
            self.init_browser()

        print(f"\n🔄 Worker {self.worker_id}: Extracting variants...")

        for i, collection_url in enumerate(self.collection_urls, 1):
            print(f"\n[Worker {self.worker_id}] [{i}/{len(self.collection_urls)}]")

            variants = self.extract_variants(collection_url)
            self.products.extend(variants)

        # Save results
        output_file = f"worker_{self.worker_id}_products.json"
        error_file = f"worker_{self.worker_id}_errors.json"

        print(f"\n💾 Worker {self.worker_id}: Saving results to {output_file}...")

        with open(output_file, 'w') as f:
            json.dump(self.products, f, indent=2)

        if self.errors:
            with open(error_file, 'w') as f:
                json.dump(self.errors, f, indent=2)

        # Summary
        print("\n" + "=" * 80)
        print(f"✨ WORKER {self.worker_id} COMPLETE!")
        print("=" * 80)
        print(f"📊 Collections processed: {len(self.collection_urls)}")
        print(f"🎯 Total variants extracted: {len(self.products)}")
        print(f"❌ Errors: {len(self.errors)}")

        if self.driver:
            self.driver.quit()


if __name__ == "__main__":
    scraper = VariantScraper(WORKER_ID, TOTAL_WORKERS, TOTAL_PRODUCTS)
    scraper.run()
