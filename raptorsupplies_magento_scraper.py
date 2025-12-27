"""
Raptor Supplies Magento Product Scraper
Extracts product variant data from Magento JavaScript configuration
"""

import json
import time
import random
import os
import sys
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc
from datetime import datetime

# Environment variables
WORKER_ID = int(os.getenv('WORKER_ID', 0))
TOTAL_WORKERS = int(os.getenv('TOTAL_WORKERS', 1))
TOTAL_PRODUCTS = int(os.getenv('TOTAL_PRODUCTS', 100))
USE_BROWSER = os.getenv('USE_BROWSER', 'true').lower() == 'true'


class MagentoScraper:
    def __init__(self, worker_id, total_workers, total_products):
        self.worker_id = worker_id
        self.total_workers = total_workers
        self.total_products = total_products
        self.driver = None
        self.collection_urls = []
        self.products = []
        self.errors = []

    def init_browser(self):
        """Initialize browser"""
        print(f"🚀 Worker {self.worker_id}: Initializing browser...")
        options = uc.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        self.driver = uc.Chrome(options=options)
        print(f"✅ Worker {self.worker_id}: Browser initialized")

    def load_collection_urls(self):
        """Load URLs"""
        print(f"📁 Worker {self.worker_id}: Loading collection URLs...")

        with open('raptorsupplies_urls.json', 'r') as f:
            data = json.load(f)
            all_urls = data.get('product_urls', [])[:self.total_products]

        self.collection_urls = [url for i, url in enumerate(all_urls) if i % self.total_workers == self.worker_id]
        print(f"✅ Worker {self.worker_id}: Assigned {len(self.collection_urls)} URLs")

    def extract_json_from_script(self, script_content, patterns):
        """Extract JSON data from JavaScript"""
        for pattern in patterns:
            matches = re.finditer(pattern, script_content, re.DOTALL)
            for match in matches:
                try:
                    json_str = match.group(1)
                    return json.loads(json_str)
                except:
                    continue
        return None

    def scrape_magento_product(self, url):
        """Scrape product using Magento-specific extraction"""
        try:
            print(f"\n   📄 Worker {self.worker_id}: {url}")

            self.driver.get(url)
            time.sleep(3)

            # Wait for Cloudflare
            if "Just a moment" in self.driver.page_source:
                time.sleep(10)

            time.sleep(2)

            # Get page source
            page_source = self.driver.page_source

            # Extract collection info
            collection_name = ""
            try:
                collection_name = self.driver.find_element(By.CSS_SELECTOR, "h1, .page-title").text.strip()
            except:
                pass

            # Strategy 1: Look for Magento configurable product JSON
            variants = []

            # Common Magento patterns for product configuration
            patterns = [
                r'var\s+spConfig\s*=\s*({.*?});',  # spConfig for configurable products
                r'window\.productData\s*=\s*({.*?});',
                r'"jsonConfig":\s*({.*?}),',
                r'<script[^>]*type="text/x-magento-init"[^>]*>(.*?)</script>',
            ]

            # Find all script tags
            scripts = self.driver.find_elements(By.TAG_NAME, "script")

            for script in scripts:
                script_content = script.get_attribute('innerHTML')
                if not script_content:
                    continue

                # Look for Magento product configuration
                if 'spConfig' in script_content or 'configurable' in script_content.lower():
                    print(f"      ✓ Found Magento config script")

                    # Try to extract JSON
                    config_data = self.extract_json_from_script(script_content, patterns)

                    if config_data:
                        print(f"      ✓ Parsed config JSON")
                        variants.extend(self.parse_magento_config(config_data, url, collection_name))
                        break

                # Look for simple product list in JSON
                if '"items"' in script_content and '"sku"' in script_content:
                    print(f"      ✓ Found product items in script")

                    # Try to extract product list
                    try:
                        # Find JSON objects with SKU
                        json_matches = re.findall(r'{[^{}]*"sku"[^{}]*}', script_content)
                        for json_str in json_matches:
                            try:
                                item = json.loads(json_str)
                                if 'sku' in item:
                                    variant = {
                                        "url": url,
                                        "collection_name": collection_name,
                                        "name": item.get('name', collection_name),
                                        "sku": item.get('sku'),
                                        "price": item.get('price'),
                                        "price_text": f"${item.get('price')}" if item.get('price') else None,
                                        "image": item.get('image'),
                                        "specifications": {},
                                        "scraped_at": datetime.now().isoformat(),
                                        "worker_id": self.worker_id
                                    }
                                    variants.append(variant)
                                    print(f"         - SKU: {variant['sku']}, Price: {variant['price_text']}")
                            except:
                                continue
                    except Exception as e:
                        print(f"         Error parsing items: {str(e)[:50]}")

            # Strategy 2: Parse JSON-LD structured data
            json_ld_scripts = self.driver.find_elements(By.CSS_SELECTOR, 'script[type="application/ld+json"]')
            for script in json_ld_scripts:
                try:
                    json_content = script.get_attribute('innerHTML')
                    data = json.loads(json_content)

                    if isinstance(data, dict):
                        # Check for product data
                        if data.get('@type') == 'Product':
                            print(f"      ✓ Found JSON-LD Product")
                            variant = self.parse_json_ld_product(data, url, collection_name)
                            if variant:
                                variants.append(variant)
                except:
                    continue

            # If no variants found, create one entry
            if not variants:
                print(f"      ⚠️  No variants found, using collection data")
                variants.append({
                    "url": url,
                    "collection_name": collection_name,
                    "name": collection_name,
                    "sku": None,
                    "price": None,
                    "price_text": None,
                    "image": None,
                    "specifications": {},
                    "scraped_at": datetime.now().isoformat(),
                    "worker_id": self.worker_id
                })

            print(f"   ✅ Worker {self.worker_id}: Extracted {len(variants)} variants")

            time.sleep(random.uniform(3, 6))
            return variants

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(f"   ❌ Worker {self.worker_id}: {error_msg}")
            self.errors.append({"url": url, "error": error_msg, "timestamp": datetime.now().isoformat()})
            return []

    def parse_magento_config(self, config, url, collection_name):
        """Parse Magento spConfig data"""
        variants = []

        try:
            # Magento spConfig structure varies, try different paths
            if 'optionPrices' in config:
                for product_id, price_data in config['optionPrices'].items():
                    variant = {
                        "url": url,
                        "collection_name": collection_name,
                        "name": config.get('productName', collection_name),
                        "sku": product_id,
                        "price": price_data.get('finalPrice', {}).get('amount') if isinstance(price_data, dict) else None,
                        "price_text": None,
                        "image": None,
                        "specifications": {},
                        "scraped_at": datetime.now().isoformat(),
                        "worker_id": self.worker_id
                    }
                    if variant["price"]:
                        variant["price_text"] = f"${variant['price']}"
                    variants.append(variant)
                    print(f"         - SKU: {variant['sku']}, Price: {variant['price_text']}")

            # Try index structure
            elif 'index' in config:
                for product_id, product_data in config['index'].items():
                    variant = {
                        "url": url,
                        "collection_name": collection_name,
                        "name": product_data.get('name', collection_name),
                        "sku": product_data.get('sku', product_id),
                        "price": product_data.get('price'),
                        "price_text": f"${product_data.get('price')}" if product_data.get('price') else None,
                        "image": product_data.get('image'),
                        "specifications": {},
                        "scraped_at": datetime.now().isoformat(),
                        "worker_id": self.worker_id
                    }
                    variants.append(variant)
                    print(f"         - SKU: {variant['sku']}, Price: {variant['price_text']}")

        except Exception as e:
            print(f"      Error parsing Magento config: {str(e)[:50]}")

        return variants

    def parse_json_ld_product(self, data, url, collection_name):
        """Parse JSON-LD product data"""
        try:
            # Handle offers
            offers = data.get('offers', {})
            if isinstance(offers, list):
                offers = offers[0] if offers else {}

            variant = {
                "url": data.get('url', url),
                "collection_name": collection_name,
                "name": data.get('name', collection_name),
                "sku": data.get('sku'),
                "price": float(offers.get('price')) if offers.get('price') else None,
                "price_text": offers.get('price'),
                "image": data.get('image'),
                "specifications": {},
                "in_stock": offers.get('availability') == 'https://schema.org/InStock',
                "scraped_at": datetime.now().isoformat(),
                "worker_id": self.worker_id
            }

            if variant['price_text'] and not variant['price_text'].startswith('$'):
                variant['price_text'] = f"${variant['price_text']}"

            print(f"         - SKU: {variant['sku']}, Price: {variant['price_text']}")
            return variant

        except Exception as e:
            print(f"      Error parsing JSON-LD: {str(e)[:50]}")
            return None

    def run(self):
        """Run scraper"""
        print("=" * 80)
        print(f"🔍 WORKER {self.worker_id} - MAGENTO SCRAPER")
        print("=" * 80)

        self.load_collection_urls()

        if not self.collection_urls:
            print(f"⚠️  Worker {self.worker_id}: No URLs assigned")
            return

        if USE_BROWSER:
            self.init_browser()

        print(f"\n🔄 Worker {self.worker_id}: Scraping products...")

        for i, url in enumerate(self.collection_urls, 1):
            print(f"\n[Worker {self.worker_id}] [{i}/{len(self.collection_urls)}]")
            variants = self.scrape_magento_product(url)
            self.products.extend(variants)

        # Save results
        output_file = f"worker_{self.worker_id}_products.json"
        error_file = f"worker_{self.worker_id}_errors.json"

        print(f"\n💾 Worker {self.worker_id}: Saving to {output_file}...")

        with open(output_file, 'w') as f:
            json.dump(self.products, f, indent=2)

        if self.errors:
            with open(error_file, 'w') as f:
                json.dump(self.errors, f, indent=2)

        print("\n" + "=" * 80)
        print(f"✨ WORKER {self.worker_id} COMPLETE!")
        print("=" * 80)
        print(f"📊 Collections: {len(self.collection_urls)}")
        print(f"🎯 Variants: {len(self.products)}")
        print(f"❌ Errors: {len(self.errors)}")

        if self.driver:
            self.driver.quit()


if __name__ == "__main__":
    scraper = MagentoScraper(WORKER_ID, TOTAL_WORKERS, TOTAL_PRODUCTS)
    scraper.run()
