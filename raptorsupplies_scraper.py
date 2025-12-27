#!/usr/bin/env python3
"""
Raptor Supplies Scraper
Advanced scraper with anti-ban protection for raptorsupplies.com
"""

import requests
import time
import random
import json
import yaml
import logging
import re
from typing import Dict, List, Optional
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin, urlparse

# Setup logging
Path("./logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('./logs/raptorsupplies_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class RaptorSuppliesScraper:
    """
    Scraper for raptorsupplies.com with:
    - Advanced anti-ban protection
    - User agent rotation
    - Session management
    - Intelligent rate limiting
    - Checkpoint system
    - Retry logic with exponential backoff
    """

    def __init__(self, config_path: str = "raptorsupplies_config.yml"):
        """Initialize scraper with configuration"""

        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # Session management
        self.session = None
        self.requests_in_session = 0
        self.session_start_time = None
        self.last_request_time = 0

        # Rate limiting
        self.consecutive_errors = 0
        self.ban_detected = False
        self.cooldown_until = 0

        # Statistics
        self.stats = {
            'total_requests': 0,
            'successful_scrapes': 0,
            'failed_scrapes': 0,
            'products_scraped': 0,
            'http_200': 0,
            'http_403': 0,
            'http_404': 0,
            'http_other': 0,
            'timeouts': 0,
            'bans_detected': 0
        }

        # Checkpoint management
        self.checkpoint_file = Path(self.config['scraping']['resume']['checkpoint_file'])
        self.checkpoint = self._load_checkpoint()

        # Create data directories
        for dir_path in [
            self.config['storage']['data_dir'],
            self.config['storage']['results_dir'],
            self.config['storage']['errors_dir'],
            self.config['storage']['checkpoints_dir']
        ]:
            Path(dir_path).mkdir(parents=True, exist_ok=True)

        logger.info("="*70)
        logger.info("RAPTOR SUPPLIES SCRAPER INITIALIZED")
        logger.info("="*70)
        logger.info(f"Base URL: {self.config['source']['base_url']}")
        logger.info(f"Rate limit: {self.config['rate_limiting']['products_per_minute']}/min")
        logger.info(f"Max workers: {self.config['scraping']['max_workers']}")
        logger.info("="*70)

    def _load_checkpoint(self) -> Dict:
        """Load scraping checkpoint"""
        if self.checkpoint_file.exists():
            with open(self.checkpoint_file, 'r') as f:
                checkpoint = json.load(f)
                logger.info(f"📋 Loaded checkpoint: {checkpoint.get('products_scraped', 0)} products processed")
                return checkpoint
        return {
            'last_product_id': 0,
            'products_scraped': 0,
            'timestamp': None,
            'failed_ids': []
        }

    def _save_checkpoint(self):
        """Save scraping checkpoint"""
        self.checkpoint['timestamp'] = datetime.now().isoformat()
        self.checkpoint['stats'] = self.stats.copy()

        with open(self.checkpoint_file, 'w') as f:
            json.dump(self.checkpoint, f, indent=2)

    def _get_session(self) -> requests.Session:
        """Get or create session with rotation"""
        max_requests = self.config['rate_limiting']['requests_per_session']

        # Create new session if needed
        if (self.session is None or self.requests_in_session >= max_requests):

            if self.session:
                self.session.close()
                logger.info(f"🔄 Rotating session after {self.requests_in_session} requests")

            self.session = requests.Session()
            self.requests_in_session = 0
            self.session_start_time = time.time()

            # Set headers with random user agent
            self.session.headers.update(self._get_headers())

        return self.session

    def _get_headers(self) -> Dict[str, str]:
        """Get randomized headers"""
        user_agents = self.config['requests']['user_agents']
        user_agent = random.choice(user_agents)

        headers = dict(self.config['requests']['headers'])
        headers['User-Agent'] = user_agent

        # Add referer occasionally (makes requests look more natural)
        if random.random() < 0.3:
            headers['Referer'] = self.config['source']['base_url']

        return headers

    def _apply_rate_limit(self):
        """Apply rate limiting with random delay"""
        min_delay = self.config['rate_limiting']['min_delay_seconds']
        max_delay = self.config['rate_limiting']['max_delay_seconds']

        # Calculate time since last request
        time_since_last = time.time() - self.last_request_time

        # Random delay within range
        delay = random.uniform(min_delay, max_delay)

        # Wait remaining time
        if time_since_last < delay:
            wait_time = delay - time_since_last
            logger.debug(f"⏳ Rate limiting: waiting {wait_time:.2f}s")
            time.sleep(wait_time)

        self.last_request_time = time.time()

    def _check_ban_status(self):
        """Check if we're in cooldown period"""
        if self.ban_detected:
            current_time = time.time()
            if current_time < self.cooldown_until:
                remaining = int(self.cooldown_until - current_time)
                logger.warning(f"🚫 Ban detected - cooling down for {remaining}s")
                return False
            else:
                logger.info("✅ Cooldown period ended, resuming scraping")
                self.ban_detected = False
                self.consecutive_errors = 0
        return True

    def _handle_error(self, product_id: int, error_type: str, error_msg: str):
        """Handle scraping errors with backoff logic"""
        self.consecutive_errors += 1
        self.stats['failed_scrapes'] += 1

        # Save error details
        error_data = {
            'product_id': product_id,
            'error_type': error_type,
            'error_msg': error_msg,
            'timestamp': datetime.now().isoformat(),
            'consecutive_errors': self.consecutive_errors
        }

        error_file = Path(self.config['storage']['errors_dir']) / f"error_{product_id}.json"
        with open(error_file, 'w') as f:
            json.dump(error_data, f, indent=2)

        # Check if we should trigger ban detection
        check_threshold = self.config['rate_limiting']['ban_detection']['check_after_errors']

        if self.consecutive_errors >= check_threshold:
            logger.error(f"⚠️  {self.consecutive_errors} consecutive errors - triggering cooldown")
            self.ban_detected = True
            cooldown = self.config['rate_limiting']['ban_detection']['cooldown_period']
            self.cooldown_until = time.time() + cooldown
            self.stats['bans_detected'] += 1
            logger.warning(f"🚫 Entering cooldown period for {cooldown}s")

    def scrape_product(self, product_id: int) -> Optional[Dict]:
        """
        Scrape a single product
        Returns: product data dict or None if failed
        """

        # Check ban status
        if not self._check_ban_status():
            time.sleep(10)  # Brief sleep before returning
            return None

        # Apply rate limiting
        self._apply_rate_limit()

        # Build URL - you may need to adjust this pattern
        url = self.config['source']['product_url_pattern'].format(product_id=product_id)

        # Get session
        session = self._get_session()
        self.requests_in_session += 1
        self.stats['total_requests'] += 1

        # Make request with retry logic
        max_retries = self.config['rate_limiting']['ban_detection']['max_retries']

        for attempt in range(max_retries):
            try:
                logger.debug(f"🌐 Requesting: {url} (attempt {attempt + 1}/{max_retries})")

                response = session.get(
                    url,
                    timeout=self.config['requests']['timeout'],
                    allow_redirects=True
                )

                # Update stats
                status = response.status_code

                if status == 200:
                    self.stats['http_200'] += 1
                elif status == 403:
                    self.stats['http_403'] += 1
                elif status == 404:
                    self.stats['http_404'] += 1
                else:
                    self.stats['http_other'] += 1

                # Handle status codes
                if status == 404:
                    logger.debug(f"   Product {product_id} not found (404)")
                    self.consecutive_errors = 0  # 404 is not an error
                    return None

                if status == 403:
                    logger.warning(f"   Product {product_id} returned 403 Forbidden")
                    self._handle_error(product_id, 'HTTP_403', 'Forbidden')

                    # Wait longer before retry
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 30
                        logger.info(f"   Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                        continue
                    return None

                if status != 200:
                    logger.warning(f"   Product {product_id} returned HTTP {status}")
                    self._handle_error(product_id, f'HTTP_{status}', f'HTTP {status}')

                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 10
                        time.sleep(wait_time)
                        continue
                    return None

                # Success! Parse product data
                product_data = self._parse_product(response.text, product_id, url)

                if product_data:
                    self.stats['successful_scrapes'] += 1
                    self.stats['products_scraped'] += 1
                    self.consecutive_errors = 0  # Reset error counter

                    # Update checkpoint
                    self.checkpoint['last_product_id'] = product_id
                    self.checkpoint['products_scraped'] = self.stats['products_scraped']

                    # Save checkpoint periodically
                    if self.stats['products_scraped'] % self.config['scraping']['checkpoint_interval'] == 0:
                        self._save_checkpoint()
                        logger.info(f"💾 Checkpoint saved at product {product_id}")

                return product_data

            except requests.exceptions.Timeout:
                logger.warning(f"   Product {product_id} timeout")
                self.stats['timeouts'] += 1
                self._handle_error(product_id, 'TIMEOUT', 'Request timeout')

                if attempt < max_retries - 1:
                    time.sleep((attempt + 1) * 5)
                    continue
                return None

            except Exception as e:
                logger.error(f"   Product {product_id} error: {e}")
                self._handle_error(product_id, 'EXCEPTION', str(e))

                if attempt < max_retries - 1:
                    time.sleep((attempt + 1) * 5)
                    continue
                return None

        return None

    def _parse_product(self, html: str, product_id: int, url: str) -> Optional[Dict]:
        """
        Parse product data from HTML
        NOTE: You'll need to customize this based on raptorsupplies.com's actual HTML structure
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')

            product = {
                'product_id': product_id,
                'url': url,
                'scraped_at': datetime.now().isoformat()
            }

            # Extract product name (adjust selectors based on actual HTML)
            name_selectors = [
                'h1.product-title',
                'h1.product-name',
                'h1[itemprop="name"]',
                '.product-details h1',
                'h1.product-single__title'
            ]

            for selector in name_selectors:
                name_elem = soup.select_one(selector)
                if name_elem:
                    product['name'] = name_elem.get_text(strip=True)
                    break

            # Extract price (adjust selectors)
            price_selectors = [
                '.product-price',
                '[itemprop="price"]',
                '.price',
                '.product__price',
                'span.money'
            ]

            for selector in price_selectors:
                price_elem = soup.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    # Extract numeric price
                    price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                    if price_match:
                        try:
                            product['price'] = float(price_match.group())
                        except:
                            product['price_text'] = price_text
                    break

            # Extract description
            desc_selectors = [
                '.product-description',
                '[itemprop="description"]',
                '.product__description',
                '.product-single__description'
            ]

            for selector in desc_selectors:
                desc_elem = soup.select_one(selector)
                if desc_elem:
                    product['description'] = desc_elem.get_text(strip=True)
                    break

            # Extract images
            img_selectors = [
                '.product-image img',
                '[itemprop="image"]',
                '.product__img',
                '.product-single__photo img'
            ]

            images = []
            for selector in img_selectors:
                for img in soup.select(selector):
                    img_url = img.get('src') or img.get('data-src')
                    if img_url:
                        # Convert to absolute URL
                        img_url = urljoin(url, img_url)
                        images.append(img_url)

            if images:
                product['images'] = images
                product['main_image'] = images[0]

            # Extract SKU
            sku_selectors = [
                '[itemprop="sku"]',
                '.product-sku',
                '.product__sku'
            ]

            for selector in sku_selectors:
                sku_elem = soup.select_one(selector)
                if sku_elem:
                    product['sku'] = sku_elem.get_text(strip=True)
                    break

            # Extract brand
            brand_selectors = [
                '[itemprop="brand"]',
                '.product-brand',
                '.product__vendor'
            ]

            for selector in brand_selectors:
                brand_elem = soup.select_one(selector)
                if brand_elem:
                    brand_text = brand_elem.get_text(strip=True)
                    product['brand'] = brand_text
                    break

            # Extract availability
            if soup.find(text=re.compile(r'out of stock', re.I)):
                product['availability'] = 'Out of Stock'
            elif soup.find(text=re.compile(r'in stock', re.I)):
                product['availability'] = 'In Stock'
            else:
                product['availability'] = 'Unknown'

            # Extract category from breadcrumbs
            breadcrumb = soup.select_one('.breadcrumb, nav[aria-label="breadcrumb"]')
            if breadcrumb:
                categories = [a.get_text(strip=True) for a in breadcrumb.select('a')]
                if categories:
                    product['category'] = ' > '.join(categories)

            # Validate we got at least a name
            if 'name' not in product or not product['name']:
                logger.warning(f"   Product {product_id} missing name - skipping")
                return None

            return product

        except Exception as e:
            logger.error(f"   Error parsing product {product_id}: {e}")
            return None

    def scrape_range(self, start_id: int, end_id: int) -> List[Dict]:
        """
        Scrape a range of products
        Returns: list of scraped products
        """
        products = []

        logger.info("="*70)
        logger.info(f"🚀 STARTING SCRAPE")
        logger.info(f"   Range: {start_id} to {end_id}")
        logger.info(f"   Total products: {end_id - start_id + 1:,}")
        logger.info("="*70)

        for product_id in range(start_id, end_id + 1):
            product = self.scrape_product(product_id)

            if product:
                products.append(product)
                logger.info(f"✅ {product_id}: {product.get('name', 'Unknown')[:60]}")

                # Save product immediately
                self._save_product(product)
            else:
                logger.debug(f"⏭️  {product_id}: Skipped")

            # Progress logging
            progress = (product_id - start_id + 1) / (end_id - start_id + 1) * 100
            if (product_id - start_id + 1) % 10 == 0:
                logger.info(f"📊 Progress: {progress:.1f}% ({len(products)} products)")
                self._print_stats()

        logger.info("="*70)
        logger.info(f"✅ SCRAPE COMPLETE")
        logger.info(f"   Products scraped: {len(products)}")
        logger.info("="*70)

        return products

    def _save_product(self, product: Dict):
        """Save individual product to file"""
        product_id = product['product_id']
        filename = f"product_{product_id}.json"
        filepath = Path(self.config['storage']['results_dir']) / filename

        with open(filepath, 'w') as f:
            json.dump(product, f, indent=2)

    def _print_stats(self):
        """Print current statistics"""
        total = self.stats['total_requests']
        success_rate = (self.stats['successful_scrapes'] / max(total, 1)) * 100

        logger.info(f"   📈 Stats: {self.stats['products_scraped']} products | "
                   f"{success_rate:.1f}% success | "
                   f"403s: {self.stats['http_403']} | "
                   f"404s: {self.stats['http_404']}")

    def get_stats(self) -> Dict:
        """Get scraping statistics"""
        total = max(self.stats['total_requests'], 1)
        return {
            **self.stats,
            'success_rate': (self.stats['successful_scrapes'] / total) * 100,
            'error_rate': (self.stats['failed_scrapes'] / total) * 100
        }

    def close(self):
        """Clean up resources"""
        if self.session:
            self.session.close()
        self._save_checkpoint()
        logger.info("👋 RaptorSuppliesScraper closed")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Raptor Supplies Scraper')
    parser.add_argument('--start', type=int, default=1, help='Start product ID')
    parser.add_argument('--end', type=int, default=100, help='End product ID')
    parser.add_argument('--config', type=str, default='raptorsupplies_config.yml', help='Config file')
    parser.add_argument('--output', type=str, default='raptorsupplies_products.json', help='Output file')

    args = parser.parse_args()

    # Create scraper
    scraper = RaptorSuppliesScraper(config_path=args.config)

    try:
        # Scrape products
        products = scraper.scrape_range(
            start_id=args.start,
            end_id=args.end
        )

        # Save consolidated results
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(products, f, indent=2)

        logger.info(f"💾 Saved {len(products)} products to {output_path}")

        # Print final stats
        stats = scraper.get_stats()
        print("\n" + "="*70)
        print("SCRAPING STATISTICS")
        print("="*70)
        print(f"Total requests:      {stats['total_requests']:,}")
        print(f"Successful scrapes:  {stats['successful_scrapes']:,}")
        print(f"Failed scrapes:      {stats['failed_scrapes']:,}")
        print(f"Success rate:        {stats['success_rate']:.1f}%")
        print(f"HTTP 200:            {stats['http_200']:,}")
        print(f"HTTP 403:            {stats['http_403']:,}")
        print(f"HTTP 404:            {stats['http_404']:,}")
        print(f"Timeouts:            {stats['timeouts']:,}")
        print(f"Bans detected:       {stats['bans_detected']:,}")
        print("="*70)

    finally:
        scraper.close()
