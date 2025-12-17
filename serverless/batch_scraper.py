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

        # Setup proxy - DISABLED (GitHub Actions and Azure Functions have dynamic IPs)
        self.proxy_url = None
        self.proxies = None

        # Statistics
        self.success_count = 0
        self.failed_count = 0
        self.start_time = time.time()

        # Results
        self.products = []
        self.failed_urls = []

    def generate_urls(self) -> List[str]:
        """
        Generate URLs for this batch by reading from URL file
        Downloads from GitHub releases if not available locally

        Returns:
            List of URLs to scrape
        """
        url_filename = 'all_product_urls_20251215_230531.txt'

        # Try to find URL file locally
        url_file_paths = [
            url_filename,
            f'../{url_filename}',
            os.path.join(os.path.dirname(__file__), '..', url_filename)
        ]

        url_file = None
        for path in url_file_paths:
            if os.path.exists(path):
                url_file = path
                break

        # If not found, download from GitHub releases
        if not url_file:
            logger.info("URL file not found locally, downloading from GitHub...")
            try:
                import requests
                download_url = f"https://github.com/mostafazog/MRO-Supply/releases/download/url-data-v1/{url_filename}"
                response = requests.get(download_url, timeout=300)

                if response.status_code == 200:
                    url_file = url_filename
                    with open(url_file, 'wb') as f:
                        f.write(response.content)
                    logger.info(f"Downloaded URL file from GitHub releases")
                else:
                    logger.error(f"Failed to download URL file: HTTP {response.status_code}")
                    return []

            except Exception as e:
                logger.error(f"Failed to download URL file: {e}")
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

            # Extract product data using comprehensive logic
            product = {
                'url': url,
                'name': '',
                'brand': '',
                'mpn': '',
                'sku': '',
                'price': '',
                'price_note': '',
                'category': '',
                'description': '',
                'images': [],
                'specifications': {},
                'additional_description': '',
                'documents': [],
                'related_products': [],
                'availability': '',
                'scraped_at': time.time()
            }

            # Extract from JSON-LD (structured data)
            json_ld = soup.find('script', type='application/ld+json')
            if json_ld:
                try:
                    import json as json_module
                    data = json_module.loads(json_ld.string)
                    if data.get('@type') == 'Product':
                        product['name'] = data.get('name', '')
                        product['description'] = data.get('description', '')
                        product['category'] = data.get('category', '')
                        if data.get('image'):
                            product['images'].append(data['image'])

                        offers = data.get('offers', [])
                        if isinstance(offers, list) and offers:
                            offer = offers[0]
                            product['sku'] = str(offer.get('sku', ''))
                            product['mpn'] = offer.get('mpn', '')
                            product['price'] = f"${offer.get('price', '')}"
                            product['availability'] = offer.get('availability', '')
                except (json_module.JSONDecodeError, KeyError):
                    pass

            # Extract brand
            brand_meta = soup.find('meta', {'name': 'twitter:data1'})
            if brand_meta:
                product['brand'] = brand_meta.get('content', brand_meta.get('value', ''))

            # Extract price (backup)
            if not product['price']:
                price_elem = soup.find('p', class_='price')
                if price_elem:
                    product['price'] = price_elem.get_text(strip=True)

            # Extract specifications
            spec_sections = soup.find_all('div', class_='m-accordion--item')
            for spec_section in spec_sections:
                spec_head = spec_section.find('button', class_='m-accordion--item--head')
                if spec_head and 'SPECIFICATION' in spec_head.get_text():
                    spec_body = spec_section.find('div', class_='m-accordion--item--body')
                    if spec_body:
                        grid_table = spec_body.find('div', class_='o-grid-table')
                        if grid_table:
                            grid_items = grid_table.find_all('div', class_='o-grid-item')
                            for item in grid_items:
                                key_elem = item.find('p', class_='key')
                                value_elem = item.find('p', class_='value')
                                if key_elem and value_elem:
                                    key = key_elem.get_text(strip=True)
                                    value = value_elem.get_text(strip=True)
                                    if key and value:
                                        product['specifications'][key] = value
                    break

            # Extract additional description
            additional_desc_section = soup.find('div', id='additionalDescription')
            if additional_desc_section:
                desc_body = additional_desc_section.find('div', class_='m-accordion--item--body')
                if desc_body:
                    desc_text = desc_body.get_text(separator='\n', strip=True)
                    product['additional_description'] = desc_text

            # Extract documents/software
            for section in spec_sections:
                section_head = section.find('button', class_='m-accordion--item--head')
                if section_head and 'Documents / Software' in section_head.get_text():
                    doc_body = section.find('div', class_='m-accordion--item--body')
                    if doc_body:
                        doc_items = doc_body.find_all('div', class_='documents--item')
                        for item in doc_items:
                            link = item.find('a')
                            if link:
                                doc_url = link.get('href', '')
                                doc_name = link.get_text(strip=True)
                                if doc_url:
                                    product['documents'].append({
                                        'name': doc_name,
                                        'url': doc_url
                                    })
                    break

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
