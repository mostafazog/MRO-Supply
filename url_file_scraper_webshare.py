#!/usr/bin/env python3
"""
URL File Scraper for MROSupply.com with Webshare Proxies
Reads URLs from all_product_urls_20251215_230531.txt and scrapes them
Optimized for 1.5M products with checkpoint/resume support
"""

import json
import csv
import time
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import requests
from bs4 import BeautifulSoup
from datetime import datetime


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_output/scraper_log_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class WebshareProxyManager:
    """Fetch and manage proxies from Webshare API"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.proxies = []
        self.proxy_index = 0
        self.proxy_lock = Lock()
        self.proxy_stats = {}

    def fetch_proxies(self):
        """Fetch proxies from Webshare API"""
        logger.info("Fetching proxies from Webshare API...")

        url = "https://proxy.webshare.io/api/v2/proxy/list/?mode=direct&page=1&page_size=100"
        headers = {"Authorization": f"Token {self.api_key}"}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            for proxy_data in data.get('results', []):
                proxy_address = proxy_data.get('proxy_address')
                port = proxy_data.get('port')
                username = proxy_data.get('username')
                password = proxy_data.get('password')

                if proxy_address and port:
                    proxy_url = f"http://{username}:{password}@{proxy_address}:{port}"
                    self.proxies.append({
                        'http': proxy_url,
                        'https': proxy_url,
                        'address': proxy_address
                    })
                    self.proxy_stats[proxy_address] = {'success': 0, 'failed': 0}

            logger.info(f"✅ Successfully fetched {len(self.proxies)} proxies from Webshare")
            return len(self.proxies) > 0

        except Exception as e:
            logger.error(f"❌ Failed to fetch proxies from Webshare: {e}")
            return False

    def get_next_proxy(self):
        """Get next proxy in rotation"""
        if not self.proxies:
            return None

        with self.proxy_lock:
            proxy = self.proxies[self.proxy_index % len(self.proxies)]
            self.proxy_index += 1
            return proxy

    def record_success(self, proxy_address: str):
        """Record successful proxy use"""
        if proxy_address in self.proxy_stats:
            self.proxy_stats[proxy_address]['success'] += 1

    def record_failure(self, proxy_address: str):
        """Record failed proxy use"""
        if proxy_address in self.proxy_stats:
            self.proxy_stats[proxy_address]['failed'] += 1


class URLFileScraper:
    """Scraper that reads URLs from a file and scrapes them with Webshare proxies"""

    def __init__(self, url_file: str, output_dir: str = "test_output",
                 max_workers: int = 10, webshare_api_key: str = None):
        self.url_file = Path(url_file)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.max_workers = max_workers

        self.checkpoint_file = self.output_dir / 'checkpoint_products.json'
        self.failed_file = self.output_dir / 'failed_urls.json'

        self.lock = Lock()
        self.session = requests.Session()

        # Statistics
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'rate_limited': 0,
            'start_time': time.time()
        }

        # Proxy manager
        self.proxy_manager = None
        if webshare_api_key:
            self.proxy_manager = WebshareProxyManager(webshare_api_key)
            if not self.proxy_manager.fetch_proxies():
                logger.warning("Failed to fetch proxies, will run without proxies")
                self.proxy_manager = None

        # Load checkpoint
        self.completed_urls = self.load_checkpoint()
        self.failed_urls = self.load_failed()

    def load_checkpoint(self) -> set:
        """Load completed URLs from checkpoint"""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, 'r') as f:
                    data = json.load(f)
                    logger.info(f"Loaded checkpoint: {len(data)} products already scraped")
                    return set(data.keys())
            except Exception as e:
                logger.error(f"Error loading checkpoint: {e}")
        return set()

    def load_failed(self) -> dict:
        """Load failed URLs"""
        if self.failed_file.exists():
            try:
                with open(self.failed_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading failed URLs: {e}")
        return {}

    def save_checkpoint(self, product: dict):
        """Save single product to checkpoint (append mode)"""
        try:
            # Use lock to prevent race condition with multiple workers
            with self.lock:
                # Load existing data
                if self.checkpoint_file.exists():
                    with open(self.checkpoint_file, 'r') as f:
                        data = json.load(f)
                else:
                    data = {}

                # Add new product
                data[product['url']] = product

                # Save back
                with open(self.checkpoint_file, 'w') as f:
                    json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Error saving checkpoint: {e}")

    def save_failed(self, url: str, error: str):
        """Save failed URL"""
        try:
            self.failed_urls[url] = {
                'error': error,
                'timestamp': time.time()
            }

            with open(self.failed_file, 'w') as f:
                json.dump(self.failed_urls, f, indent=2)

        except Exception as e:
            logger.error(f"Error saving failed URL: {e}")

    def load_urls_from_file(self) -> List[str]:
        """Load URLs from file"""
        logger.info(f"Loading URLs from {self.url_file}...")

        urls = []
        try:
            with open(self.url_file, 'r') as f:
                for line in f:
                    url = line.strip()
                    if url and url not in self.completed_urls:
                        urls.append(url)

            logger.info(f"Loaded {len(urls):,} URLs to scrape ({len(self.completed_urls):,} already completed)")
            return urls

        except Exception as e:
            logger.error(f"Error loading URL file: {e}")
            return []

    def scrape_product(self, url: str) -> Optional[Dict]:
        """Scrape a single product"""
        proxy = None
        proxy_address = "Unknown"

        try:
            # Get proxy if available
            if self.proxy_manager:
                proxy_dict = self.proxy_manager.get_next_proxy()
                if proxy_dict:
                    proxy = proxy_dict
                    proxy_address = proxy_dict.get('address', 'Unknown')

            # Make request
            response = self.session.get(
                url,
                proxies=proxy,
                timeout=30,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                }
            )

            # Handle rate limiting
            if response.status_code == 429:
                with self.lock:
                    self.stats['rate_limited'] += 1
                if self.proxy_manager:
                    self.proxy_manager.record_failure(proxy_address)
                logger.warning(f"RATE LIMITED {url} - Proxy: {proxy_address}")
                return None

            # Handle 404
            if response.status_code == 404:
                logger.info(f"NOT FOUND {url}")
                self.save_failed(url, "HTTP 404 - Product not found")
                return None

            response.raise_for_status()

            # Parse product
            soup = BeautifulSoup(response.content, 'html.parser')
            product = self.extract_product_data(soup, url)

            # Record success
            if self.proxy_manager:
                self.proxy_manager.record_success(proxy_address)

            with self.lock:
                self.stats['success'] += 1

            # Save to checkpoint immediately
            self.save_checkpoint(product)

            logger.info(f"SUCCESS [{self.stats['success']}] {product.get('sku', 'Unknown')} {product.get('name', 'Unknown')} - {url} - Proxy: {proxy_address}")

            return product

        except Exception as e:
            with self.lock:
                self.stats['failed'] += 1

            if self.proxy_manager and proxy:
                self.proxy_manager.record_failure(proxy_address)

            error_msg = str(e)
            logger.error(f"FAILED [{self.stats['failed']}] {url} - {error_msg} - Proxy: {proxy_address}")
            self.save_failed(url, error_msg)

            return None

    def extract_product_data(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract product data from HTML"""
        product = {
            'url': url,
            'name': '',
            'sku': '',
            'brand': '',
            'price': '',
            'description': '',
            'scraped_at': datetime.now().isoformat()
        }

        # Extract from JSON-LD
        json_ld = soup.find('script', type='application/ld+json')
        if json_ld:
            try:
                data = json.loads(json_ld.string)
                product['name'] = data.get('name', '')
                product['sku'] = data.get('sku', '')
                product['brand'] = data.get('brand', {}).get('name', '')

                if 'offers' in data:
                    product['price'] = data['offers'].get('price', '')

            except Exception as e:
                logger.debug(f"Error parsing JSON-LD: {e}")

        # Fallback to HTML
        if not product['name']:
            name_elem = soup.find('h1', class_='product-name')
            if name_elem:
                product['name'] = name_elem.text.strip()

        if not product['sku']:
            sku_elem = soup.find('span', class_='product-sku')
            if sku_elem:
                product['sku'] = sku_elem.text.strip()

        return product

    def scrape_concurrent(self, urls: List[str]):
        """Scrape URLs concurrently"""
        logger.info(f"Starting concurrent scraping with {self.max_workers} workers...")

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.scrape_product, url): url for url in urls}

            for future in as_completed(futures):
                url = futures[future]

                with self.lock:
                    self.stats['total'] += 1

                    # Progress update every 100 products
                    if self.stats['total'] % 100 == 0:
                        elapsed = time.time() - self.stats['start_time']
                        rate = self.stats['total'] / elapsed
                        remaining = len(urls) - self.stats['total']
                        eta = remaining / rate if rate > 0 else 0

                        logger.info(f"Progress: {self.stats['total']:,}/{len(urls):,} ({self.stats['total']/len(urls)*100:.1f}%) | "
                                  f"Success: {self.stats['success']:,} | Failed: {self.stats['failed']:,} | "
                                  f"Rate: {rate:.1f}/s | ETA: {eta/60:.1f}min")

                        if self.proxy_manager:
                            total_reqs = sum(s['success'] + s['failed'] for s in self.proxy_manager.proxy_stats.values())
                            total_success = sum(s['success'] for s in self.proxy_manager.proxy_stats.values())
                            success_rate = (total_success / total_reqs * 100) if total_reqs > 0 else 0
                            logger.info(f"Proxy Stats - Total: {total_reqs:,}, Success Rate: {success_rate:.1f}%")

    def run(self):
        """Run the scraper"""
        logger.info("="*70)
        logger.info("URL FILE SCRAPER WITH WEBSHARE PROXIES")
        logger.info("="*70)

        # Load URLs
        urls = self.load_urls_from_file()

        if not urls:
            logger.error("No URLs to scrape!")
            return

        logger.info(f"Target: {len(urls):,} products")
        logger.info(f"Workers: {self.max_workers}")
        logger.info(f"Proxies: {'Enabled' if self.proxy_manager else 'Disabled'}")
        logger.info("="*70)

        # Scrape
        self.scrape_concurrent(urls)

        # Final summary
        elapsed = time.time() - self.stats['start_time']
        logger.info("="*70)
        logger.info(f"Scraping complete! Success: {self.stats['success']:,} | Failed: {self.stats['failed']:,} | "
                   f"Rate Limited: {self.stats['rate_limited']} | Time: {elapsed/60:.1f} minutes | "
                   f"Rate: {self.stats['success']/elapsed:.2f} products/second")

        if self.proxy_manager:
            total_reqs = sum(s['success'] + s['failed'] for s in self.proxy_manager.proxy_stats.values())
            total_success = sum(s['success'] for s in self.proxy_manager.proxy_stats.values())
            logger.info(f"Final Proxy Stats - Total Requests: {total_reqs:,}, "
                       f"Success Rate: {total_success/total_reqs*100:.1f}%")

        logger.info("="*70)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='URL File Scraper with Webshare Proxies')
    parser.add_argument('--url-file', type=str, required=True, help='Path to URL file')
    parser.add_argument('--output-dir', type=str, default='test_output', help='Output directory')
    parser.add_argument('--workers', type=int, default=10, help='Number of concurrent workers')
    parser.add_argument('--webshare-api-key', type=str, help='Webshare API key (from env if not provided)')

    args = parser.parse_args()

    # Get API key from args or environment
    api_key = args.webshare_api_key or os.getenv('WEBSHARE_API_KEY')

    if not api_key:
        logger.warning("No Webshare API key provided, running without proxies")

    scraper = URLFileScraper(
        url_file=args.url_file,
        output_dir=args.output_dir,
        max_workers=args.workers,
        webshare_api_key=api_key
    )

    scraper.run()


if __name__ == '__main__':
    main()
