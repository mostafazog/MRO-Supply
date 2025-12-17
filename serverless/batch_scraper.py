#!/usr/bin/env python3
"""
Batch Scraper for GitHub Actions / Azure Functions
Processes a batch of URLs in parallel serverless environment
"""

import os
import sys
import json
import time
import argparse
import logging
from pathlib import Path
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import requests
    from bs4 import BeautifulSoup
    from config import Config
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Run: pip install requests beautifulsoup4 lxml python-dotenv")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BatchScraper:
    """Scrapes a batch of URLs for serverless execution"""

    def __init__(self, batch_id: int, batch_size: int, output_dir: Path):
        """
        Initialize batch scraper

        Args:
            batch_id: Batch number
            batch_size: URLs per batch
            output_dir: Output directory
        """
        self.batch_id = batch_id
        self.batch_size = batch_size
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Load config
        try:
            self.config = Config()
        except Exception as e:
            logger.warning(f"Could not load config: {e}")
            self.config = None

        # Setup proxy
        self.proxy_url = self._get_proxy_url()
        self.proxies = {
            'http': self.proxy_url,
            'https': self.proxy_url
        } if self.proxy_url else None

        # Statistics
        self.success_count = 0
        self.failed_count = 0
        self.start_time = time.time()

        # Results
        self.products = []
        self.failed_urls = []

    def _get_proxy_url(self) -> str:
        """Get proxy URL from config or environment"""
        if self.config and hasattr(self.config, 'get_proxy_url'):
            return self.config.get_proxy_url()

        # Try environment variables
        host = os.getenv('PROXY_HOST')
        port = os.getenv('PROXY_PORT')
        user = os.getenv('PROXY_USER')
        password = os.getenv('PROXY_PASS')

        if all([host, port, user, password]):
            return f"http://{user}:{password}@{host}:{port}"

        return None

    def generate_urls(self) -> List[str]:
        """
        Generate URLs for this batch by reading from URL file

        Returns:
            List of URLs to scrape
        """
        # Try to find URL file
        url_file_paths = [
            'all_product_urls_20251215_230531.txt',
            '../all_product_urls_20251215_230531.txt',
            os.path.join(os.path.dirname(__file__), '..', 'all_product_urls_20251215_230531.txt')
        ]

        url_file = None
        for path in url_file_paths:
            if os.path.exists(path):
                url_file = path
                break

        if not url_file:
            logger.error("URL file not found!")
            return []

        # Calculate start and end for this batch
        start_idx = self.batch_id * self.batch_size
        end_idx = start_idx + self.batch_size

        urls = []

        # Read URLs from file
        try:
            with open(url_file, 'r') as f:
                all_urls = [line.strip() for line in f if line.strip()]

            # Get URLs for this batch
            urls = all_urls[start_idx:end_idx]

            logger.info(f"Loaded {len(urls)} URLs for batch {self.batch_id} (lines {start_idx}-{end_idx})")

        except Exception as e:
            logger.error(f"Failed to read URL file: {e}")
            return []

        return urls

    def scrape_product(self, url: str) -> Dict:
        """
        Scrape a single product

        Args:
            url: Product URL

        Returns:
            Product data dict or None
        """
        try:
            # Make request
            response = requests.get(
                url,
                proxies=self.proxies,
                timeout=30,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'text/html,application/xhtml+xml',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                }
            )

            if response.status_code != 200:
                logger.warning(f"HTTP {response.status_code}: {url}")
                self.failed_urls.append({
                    'url': url,
                    'error': f'HTTP {response.status_code}',
                    'timestamp': time.time()
                })
                return None

            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract product data using same logic as main scraper
            product = {
                'url': url,
                'title': '',
                'sku': '',
                'price': '',
                'availability': '',
                'description': '',
                'specifications': [],
                'images': [],
                'category': '',
                'brand': '',
                'scraped_at': time.time()
            }

            # Title - use first h1
            title_tag = soup.find('h1')
            if title_tag:
                product['title'] = title_tag.get_text(strip=True)

            # SKU - extract from URL
            url_parts = url.rstrip('/').split('/')
            if url_parts:
                last_part = url_parts[-1]
                if '_' in last_part:
                    product['sku'] = last_part.split('_')[0]

            # Price
            price_tag = soup.find('p', class_='price')
            if price_tag:
                product['price'] = price_tag.get_text(strip=True)

            # Availability
            avail_div = soup.find('div', class_=lambda x: x and 'availability' in x.lower() if x else False)
            if avail_div:
                product['availability'] = avail_div.get_text(strip=True)

            # Description - from meta tag
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                product['description'] = meta_desc.get('content', '')

            # Brand - extract from URL
            if '_' in url_parts[-1]:
                parts = url_parts[-1].split('_')
                if len(parts) >= 3:
                    product['brand'] = parts[-1].replace('-', ' ').title()

            # Images
            for img in soup.find_all('img'):
                src = img.get('src') or img.get('data-src')
                if src and ('product' in src.lower() or 'static.mrosupply' in src):
                    if 'icon' not in src and 'chevron' not in src:
                        product['images'].append(src)

            # Category - from URL path
            if len(url_parts) > 4:
                product['category'] = url_parts[3].replace('-', ' ').title()

            self.success_count += 1
            return product

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for {url}: {e}")
            self.failed_urls.append({
                'url': url,
                'error': str(e),
                'timestamp': time.time()
            })
            return None

        except Exception as e:
            logger.error(f"Parse error for {url}: {e}")
            self.failed_urls.append({
                'url': url,
                'error': f'Parse error: {str(e)}',
                'timestamp': time.time()
            })
            return None

    def _extract_text(self, soup, selector: str) -> str:
        """Extract text from element"""
        try:
            element = soup.select_one(selector)
            return element.get_text(strip=True) if element else ''
        except:
            return ''

    def _extract_images(self, soup) -> List[str]:
        """Extract image URLs"""
        try:
            images = []
            for img in soup.select('img.product-image'):
                src = img.get('src') or img.get('data-src')
                if src:
                    images.append(src)
            return images
        except:
            return []

    def _extract_specs(self, soup) -> Dict:
        """Extract specifications"""
        try:
            specs = {}
            for row in soup.select('table.specs tr'):
                cells = row.select('td')
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    specs[key] = value
            return specs
        except:
            return {}

    def scrape_batch(self, max_workers: int = 5):
        """
        Scrape all URLs in batch

        Args:
            max_workers: Number of concurrent workers
        """
        logger.info(f"Starting batch {self.batch_id} with {max_workers} workers")

        # Generate URLs
        urls = self.generate_urls()

        # Scrape in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.scrape_product, url): url
                for url in urls
            }

            for future in as_completed(futures):
                url = futures[future]
                try:
                    product = future.result()
                    if product:
                        self.products.append(product)

                    # Progress logging
                    total = len(urls)
                    completed = self.success_count + self.failed_count
                    if completed % 50 == 0:
                        logger.info(
                            f"Batch {self.batch_id}: {completed}/{total} "
                            f"({completed/total*100:.1f}%) - "
                            f"Success: {self.success_count}, Failed: {self.failed_count}"
                        )

                except Exception as e:
                    logger.error(f"Future error for {url}: {e}")
                    self.failed_count += 1

        # Calculate statistics
        elapsed = time.time() - self.start_time
        total = self.success_count + self.failed_count
        success_rate = (self.success_count / total * 100) if total > 0 else 0

        logger.info(f"Batch {self.batch_id} completed:")
        logger.info(f"  Success: {self.success_count}")
        logger.info(f"  Failed: {self.failed_count}")
        logger.info(f"  Success rate: {success_rate:.1f}%")
        logger.info(f"  Duration: {elapsed:.1f}s")
        logger.info(f"  Speed: {self.success_count/elapsed:.2f} products/sec")

    def save_results(self):
        """Save results to files"""
        # Save products JSON
        json_file = self.output_dir / f"batch_{self.batch_id}_products.json"
        with open(json_file, 'w') as f:
            json.dump(self.products, f, indent=2)

        logger.info(f"Saved {len(self.products)} products to {json_file}")

        # Save products CSV
        csv_file = self.output_dir / f"batch_{self.batch_id}_products.csv"
        self._save_csv(csv_file)

        # Save failed URLs
        if self.failed_urls:
            failed_file = self.output_dir / f"batch_{self.batch_id}_failed.json"
            with open(failed_file, 'w') as f:
                json.dump(self.failed_urls, f, indent=2)

            logger.info(f"Saved {len(self.failed_urls)} failed URLs to {failed_file}")

        # Save metadata
        metadata = {
            'batch_id': self.batch_id,
            'batch_size': self.batch_size,
            'success_count': self.success_count,
            'failed_count': self.failed_count,
            'success_rate': (self.success_count / (self.success_count + self.failed_count) * 100)
                           if (self.success_count + self.failed_count) > 0 else 0,
            'duration_seconds': time.time() - self.start_time,
            'timestamp': time.time()
        }

        metadata_file = self.output_dir / f"batch_{self.batch_id}_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

    def _save_csv(self, csv_file: Path):
        """Save products to CSV"""
        import csv

        if not self.products:
            return

        # Get all keys
        all_keys = set()
        for product in self.products:
            all_keys.update(product.keys())

        # Write CSV
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=sorted(all_keys))
            writer.writeheader()

            for product in self.products:
                # Flatten nested dicts
                row = {}
                for key, value in product.items():
                    if isinstance(value, (dict, list)):
                        row[key] = json.dumps(value)
                    else:
                        row[key] = value
                writer.writerow(row)

        logger.info(f"Saved CSV to {csv_file}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Batch scraper for serverless execution')
    parser.add_argument('--batch-id', type=int, required=True, help='Batch ID')
    parser.add_argument('--batch-size', type=int, default=500, help='URLs per batch')
    parser.add_argument('--output-dir', type=str, default='./output', help='Output directory')
    parser.add_argument('--workers', type=int, default=5, help='Concurrent workers')

    args = parser.parse_args()

    try:
        # Create scraper
        scraper = BatchScraper(
            batch_id=args.batch_id,
            batch_size=args.batch_size,
            output_dir=Path(args.output_dir)
        )

        # Scrape batch
        scraper.scrape_batch(max_workers=args.workers)

        # Save results
        scraper.save_results()

        # Exit with success
        sys.exit(0)

    except Exception as e:
        logger.error(f"Batch scraper failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
