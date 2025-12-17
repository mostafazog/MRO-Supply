#!/usr/bin/env python3
"""
MRO Supply Product Scraper - Rotating Residential Proxy
Scrapes all 1.5M products using Webshare rotating residential proxies
"""

import json
import csv
import time
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import argparse
import logging


class RotatingResidentialScraper:
    """Scraper using Webshare Rotating Residential Proxy"""

    def __init__(self, proxy_host: str, proxy_port: int, proxy_user: str, proxy_pass: str,
                 output_dir: str = "scraped_data", workers: int = 20, delay: float = 0.3,
                 rate_limit_threshold: int = 10, cooldown_minutes: int = 15):
        """
        Initialize scraper with rotating residential proxy

        Args:
            proxy_host: Proxy host (e.g., p.webshare.io)
            proxy_port: Proxy port (e.g., 10000)
            proxy_user: Proxy username
            proxy_pass: Proxy password
            output_dir: Directory to save scraped data
            workers: Number of concurrent workers
            delay: Delay between requests in seconds
            rate_limit_threshold: Number of 429 errors before pausing (default: 10)
            cooldown_minutes: Minutes to wait when rate limited (default: 15)
        """
        self.proxy_url = f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}"
        self.proxies = {
            'http': self.proxy_url,
            'https': self.proxy_url
        }
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.workers = workers
        self.delay = delay

        # Thread-safe counters
        self.success_count = 0
        self.failed_count = 0
        self.lock = Lock()

        # Rate limit tracking
        self.rate_limit_count = 0
        self.last_rate_limit_time = None
        self.is_paused = False
        self.rate_limit_threshold = rate_limit_threshold
        self.cooldown_minutes = cooldown_minutes

        # Proxy usage tracking
        self.total_requests = 0
        self.proxy_ips_seen = set()
        self.requests_by_status = {
            'success': 0,
            'rate_limited': 0,
            'timeout': 0,
            'proxy_error': 0,
            'connection_error': 0,
            'other_error': 0
        }
        self.start_time = None

        # Results storage
        self.products = []
        self.failed_urls = []
        self.errors = []  # Store detailed error information
        self.scraped_urls = set()  # Track already scraped URLs

        # Setup logging
        self.log_file = self.output_dir / f"scraper_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self.error_file = self.output_dir / "errors.jsonl"

        # Configure logging to file only (console output is handled separately)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.handlers = []  # Clear any existing handlers

        # File handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(file_handler)

        # Prevent propagation to root logger
        self.logger.propagate = False

        print(f"✅ Initialized Rotating Residential Scraper")
        print(f"   Proxy: {proxy_host}:{proxy_port}")
        print(f"   Workers: {workers}")
        print(f"   Delay: {delay}s")
        print(f"   Rate Limit Protection: Pause after {rate_limit_threshold} 429s for {cooldown_minutes}min")
        print(f"   Output: {output_dir}/")
        print(f"   Log: {self.log_file.name}")
        print(f"   Errors: {self.error_file.name}")

    def load_checkpoint(self) -> bool:
        """Load checkpoint data to resume scraping"""
        checkpoint_json = self.output_dir / "checkpoint_products.json"

        if not checkpoint_json.exists():
            print("ℹ️  No checkpoint found, starting fresh")
            return False

        try:
            with open(checkpoint_json, 'r', encoding='utf-8') as f:
                self.products = json.load(f)

            # Track already scraped URLs
            self.scraped_urls = {p['url'] for p in self.products}
            self.success_count = len(self.products)

            print(f"✅ Loaded checkpoint: {self.success_count:,} products already scraped")
            self.logger.info(f"Resumed from checkpoint: {self.success_count:,} products")
            return True

        except Exception as e:
            print(f"⚠️  Failed to load checkpoint: {e}")
            self.logger.error(f"Failed to load checkpoint: {e}")
            return False

    def load_failed_urls(self) -> List[str]:
        """Load failed URLs from errors.jsonl for retry"""
        if not self.error_file.exists():
            return []

        failed_urls = []
        try:
            with open(self.error_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        error_record = json.loads(line)
                        failed_urls.append(error_record['url'])

            print(f"✅ Loaded {len(failed_urls):,} failed URLs for retry")
            self.logger.info(f"Loaded {len(failed_urls):,} failed URLs for retry")
            return failed_urls

        except Exception as e:
            print(f"⚠️  Failed to load error file: {e}")
            self.logger.error(f"Failed to load error file: {e}")
            return []

    def handle_rate_limit(self):
        """Handle rate limiting with cooldown period"""
        with self.lock:
            self.rate_limit_count += 1
            self.last_rate_limit_time = time.time()

            if self.rate_limit_count >= self.rate_limit_threshold:
                self.is_paused = True

                msg = (f"🚨 RATE LIMIT: {self.rate_limit_count} consecutive 429 errors detected! "
                       f"Pausing for {self.cooldown_minutes} minutes to let proxy pool rotate...")
                print(f"\n{'='*70}")
                print(msg)
                print(f"{'='*70}\n")
                self.logger.warning(msg)

                # Wait for cooldown period
                for remaining in range(self.cooldown_minutes * 60, 0, -30):
                    mins, secs = divmod(remaining, 60)
                    print(f"⏳ Cooldown: {mins}m {secs}s remaining...", end='\r')
                    time.sleep(30)

                print("\n✅ Cooldown complete! Resuming scraping...")
                self.logger.info("Cooldown complete, resuming scraping")

                # Reset counters
                self.rate_limit_count = 0
                self.is_paused = False

    def reset_rate_limit_counter(self):
        """Reset rate limit counter on successful request"""
        with self.lock:
            if self.rate_limit_count > 0:
                self.rate_limit_count = 0

    def get_proxy_stats(self) -> str:
        """Get formatted proxy statistics"""
        if self.total_requests == 0:
            return "No requests yet"

        elapsed = time.time() - self.start_time if self.start_time else 1
        req_per_sec = self.total_requests / elapsed if elapsed > 0 else 0

        success_rate = (self.requests_by_status['success'] / self.total_requests * 100) if self.total_requests > 0 else 0

        stats = [
            f"📊 Proxy Stats:",
            f"   Total Requests: {self.total_requests:,}",
            f"   Request Rate: {req_per_sec:.2f} req/s",
            f"   Unique IPs: {len(self.proxy_ips_seen):,}",
            f"   Success: {self.requests_by_status['success']:,} ({success_rate:.1f}%)",
        ]

        # Add error breakdown if there are errors
        if self.requests_by_status['rate_limited'] > 0:
            stats.append(f"   Rate Limited: {self.requests_by_status['rate_limited']:,}")
        if self.requests_by_status['timeout'] > 0:
            stats.append(f"   Timeouts: {self.requests_by_status['timeout']:,}")
        if self.requests_by_status['proxy_error'] > 0:
            stats.append(f"   Proxy Errors: {self.requests_by_status['proxy_error']:,}")
        if self.requests_by_status['connection_error'] > 0:
            stats.append(f"   Connection Errors: {self.requests_by_status['connection_error']:,}")
        if self.requests_by_status['other_error'] > 0:
            stats.append(f"   Other Errors: {self.requests_by_status['other_error']:,}")

        return '\n'.join(stats)

    def get_headers(self) -> Dict[str, str]:
        """Get random headers"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        ]
        
        return {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }

    def scrape_product(self, url: str, retry: int = 3) -> Tuple[Optional[Dict], Optional[str], Optional[str]]:
        """Scrape a single product page with retries

        Returns:
            Tuple of (product_data, error_message, proxy_ip)
        """
        last_error = None
        proxy_ip = None

        for attempt in range(retry):
            try:
                # Track request
                with self.lock:
                    self.total_requests += 1

                response = requests.get(
                    url,
                    proxies=self.proxies,
                    headers=self.get_headers(),
                    timeout=45,  # Increased from 30s
                    allow_redirects=True
                )

                # Extract proxy IP from response headers (if available)
                proxy_ip = response.headers.get('X-Forwarded-For',
                             response.headers.get('X-Real-IP', 'Unknown'))

                # Track unique proxy IPs
                if proxy_ip and proxy_ip != 'Unknown':
                    with self.lock:
                        self.proxy_ips_seen.add(proxy_ip.split(',')[0].strip())

                if response.status_code == 200:
                    # Success - reset rate limit counter
                    self.reset_rate_limit_counter()

                    with self.lock:
                        self.requests_by_status['success'] += 1

                    soup = BeautifulSoup(response.content, 'html.parser') # type: ignore

                    # Extract product data
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
                        'scraped_at': datetime.now().isoformat()
                    }
                    
                    # Title - use first h1
                    title_tag = soup.find('h1')
                    if title_tag:
                        product['title'] = title_tag.get_text(strip=True)
                    
                    # SKU - extract from URL or meta tags
                    # URL format: .../sku_name_brand/
                    url_parts = url.rstrip('/').split('/')
                    if url_parts:
                        last_part = url_parts[-1]
                        if '_' in last_part:
                            product['sku'] = last_part.split('_')[0]
                    
                    # Price
                    price_tag = soup.find('p', class_='price')
                    if price_tag:
                        product['price'] = price_tag.get_text(strip=True)
                    
                    # Availability - try multiple selectors
                    avail_div = soup.find('div', class_=lambda x: x and 'availability' in x.lower() if x else False)
                    if avail_div:
                        product['availability'] = avail_div.get_text(strip=True)
                    
                    # Description - from meta tag or page content
                    meta_desc = soup.find('meta', attrs={'name': 'description'})
                    if meta_desc:
                        product['description'] = meta_desc.get('content', '')
                    
                    # Brand - extract from title or URL
                    if '_' in url_parts[-1]:
                        parts = url_parts[-1].split('_')
                        if len(parts) >= 3:
                            product['brand'] = parts[-1].replace('-', ' ').title()
                    
                    # Images - find all product images
                    for img in soup.find_all('img'):
                        src = img.get('src') or img.get('data-src')
                        if src and ('product' in src.lower() or 'static.mrosupply' in src):
                            if 'icon' not in src and 'chevron' not in src:
                                product['images'].append(src)
                    
                    # Category - from breadcrumbs or URL path
                    if len(url_parts) > 4:
                        product['category'] = url_parts[3].replace('-', ' ').title()

                    return product, None, proxy_ip

                elif response.status_code == 404:
                    return None, "HTTP 404 - Product not found", proxy_ip

                elif response.status_code == 429:
                    # Rate limit detected
                    last_error = "HTTP 429 - Rate limit exceeded"

                    with self.lock:
                        self.requests_by_status['rate_limited'] += 1

                    # Trigger cooldown if threshold reached
                    self.handle_rate_limit()

                    # Wait longer before retry (proxy should have rotated)
                    if attempt < retry - 1:
                        time.sleep(10)
                        continue

                else:
                    last_error = f"HTTP {response.status_code}"
                    with self.lock:
                        self.requests_by_status['other_error'] += 1
                    if attempt < retry - 1:
                        time.sleep(3)  # Wait longer before retry
                        continue

            except requests.exceptions.Timeout:
                last_error = "Request timeout (45s)"
                with self.lock:
                    self.requests_by_status['timeout'] += 1
                if attempt < retry - 1:
                    time.sleep(3)
                    continue
            except requests.exceptions.ProxyError as e:
                last_error = f"Proxy error: {str(e)}"
                with self.lock:
                    self.requests_by_status['proxy_error'] += 1
                if attempt < retry - 1:
                    time.sleep(3)
                    continue
            except requests.exceptions.ConnectionError as e:
                last_error = f"Connection error: {str(e)}"
                with self.lock:
                    self.requests_by_status['connection_error'] += 1
                if attempt < retry - 1:
                    time.sleep(3)
                    continue
            except Exception as e:
                last_error = f"{type(e).__name__}: {str(e)}"
                with self.lock:
                    self.requests_by_status['other_error'] += 1
                if attempt < retry - 1:
                    time.sleep(3)
                    continue

        return None, last_error or "Unknown error after 3 retries", proxy_ip

    def scrape_url(self, url: str) -> bool:
        """Scrape a URL and store result"""
        # Skip if already scraped
        if url in self.scraped_urls:
            return True

        product, error, proxy_ip = self.scrape_product(url)

        with self.lock:
            if product:
                self.products.append(product)
                self.success_count += 1
                self.scraped_urls.add(url)

                # Display product info with proxy IP
                print(f"\n✅ [{self.success_count:,}] {product['title'][:80]}")
                print(f"   URL: {url}")
                print(f"   SKU: {product['sku']} | Price: {product['price']} | Brand: {product['brand']}")
                print(f"   Category: {product['category']} | Images: {len(product['images'])}")
                if proxy_ip and proxy_ip != 'Unknown':
                    print(f"   🌐 Proxy IP: {proxy_ip}")

                # Log success
                self.logger.info(f"SUCCESS [{self.success_count}] {product['title']} - {url} - Proxy: {proxy_ip}")

                # Save checkpoint every 50 products
                if self.success_count % 50 == 0:
                    self.save_checkpoint()
                    print(f"\n💾 Checkpoint saved: {self.success_count:,} products")

                return True
            else:
                self.failed_urls.append(url)
                self.failed_count += 1

                # Store error details
                error_record = {
                    'url': url,
                    'error': error,
                    'proxy_ip': proxy_ip or 'Unknown',
                    'timestamp': datetime.now().isoformat(),
                    'count': self.failed_count
                }
                self.errors.append(error_record)

                # Save error to file immediately
                with open(self.error_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(error_record) + '\n')

                # Display error with special formatting for 429
                if "429" in error:
                    print(f"\n🚫 [{self.failed_count:,}] RATE LIMITED: {url}")
                    print(f"   Error: {error} (Proxy rotating...)")
                    if proxy_ip and proxy_ip != 'Unknown':
                        print(f"   🌐 Proxy IP: {proxy_ip}")
                else:
                    print(f"\n❌ [{self.failed_count:,}] Failed: {url}")
                    print(f"   Error: {error}")
                    if proxy_ip and proxy_ip != 'Unknown':
                        print(f"   🌐 Proxy IP: {proxy_ip}")

                # Log error
                self.logger.error(f"FAILED [{self.failed_count}] {url} - {error} - Proxy: {proxy_ip}")

                return False
    
    def save_checkpoint(self):
        """Save checkpoint without timestamp (overwrites previous checkpoint)"""
        checkpoint_json = self.output_dir / "checkpoint_products.json"
        checkpoint_csv = self.output_dir / "checkpoint_products.csv"

        # Save JSON
        with open(checkpoint_json, 'w', encoding='utf-8') as f:
            json.dump(self.products, f, indent=2, ensure_ascii=False)

        # Save CSV
        if self.products:
            with open(checkpoint_csv, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'url', 'title', 'sku', 'price', 'availability', 'description',
                    'category', 'brand', 'scraped_at'
                ])
                writer.writeheader()
                for product in self.products:
                    row = {k: v for k, v in product.items() if k not in ['specifications', 'images']}
                    writer.writerow(row)

        self.logger.info(f"Checkpoint saved: {len(self.products):,} products")

    def scrape_urls(self, urls: List[str], target: Optional[int] = None):
        """Scrape multiple URLs with progress tracking"""
        # Filter out already scraped URLs
        original_count = len(urls)
        urls = [url for url in urls if url not in self.scraped_urls]
        skipped = original_count - len(urls)

        if skipped > 0:
            print(f"ℹ️  Skipping {skipped:,} already scraped URLs")
            self.logger.info(f"Skipping {skipped:,} already scraped URLs")

        if target:
            urls = urls[:target]

        total = len(urls)
        if total == 0:
            print("✅ All URLs already scraped!")
            return

        print(f"\n{'='*70}")
        print(f"Starting scrape: {total:,} URLs")
        print(f"{'='*70}\n")
        self.logger.info(f"Starting scrape: {total:,} URLs with {self.workers} workers")

        start_time = time.time()
        self.start_time = start_time  # Track for proxy stats
        submitted = 0

        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = []

            for url in urls:
                future = executor.submit(self.scrape_url, url)
                futures.append(future)
                submitted += 1

                # Show progress every 100 submitted
                if submitted % 100 == 0:
                    status_msg = (f"Submitted: {submitted:,}/{total:,} | Active workers: {self.workers} | "
                                  f"Completed: {self.success_count + self.failed_count:,} "
                                  f"(✓{self.success_count:,} ✗{self.failed_count:,}) | "
                                  f"Requests: {self.total_requests:,} | IPs: {len(self.proxy_ips_seen):,}")
                    print(status_msg)
                    self.logger.info(status_msg)

                time.sleep(self.delay)  # Rate limiting

            print(f"All {total:,} requests submitted. Waiting for completion...\n")
            self.logger.info(f"All {total:,} requests submitted")

            # Track progress
            for i, future in enumerate(as_completed(futures), 1):
                try:
                    future.result()
                except Exception as e:
                    with self.lock:
                        self.failed_count += 1

                # Progress summary every 100 products
                if i % 100 == 0 or i == total:
                    elapsed = time.time() - start_time
                    rate = i / elapsed if elapsed > 0 else 0
                    eta = (total - i) / rate if rate > 0 else 0

                    progress_msg = (f"Progress: {i:,}/{total:,} ({i/total*100:.1f}%) | "
                                    f"Success: {self.success_count:,} | Failed: {self.failed_count:,} | "
                                    f"Rate: {rate:.1f}/s | ETA: {eta/60:.1f}min")

                    print(f"\n{'─'*70}")
                    print(f"📊 {progress_msg}")
                    print(f"{'─'*70}")

                    # Show proxy stats
                    print(self.get_proxy_stats())
                    print(f"{'─'*70}")

                    self.logger.info(progress_msg)
                    self.logger.info(f"Proxy Stats - Total: {self.total_requests:,}, "
                                    f"Unique IPs: {len(self.proxy_ips_seen):,}, "
                                    f"Success Rate: {self.requests_by_status['success']/self.total_requests*100:.1f}%"
                                    if self.total_requests > 0 else "No requests yet")

        elapsed = time.time() - start_time

        # Count rate limit errors
        rate_limit_errors = sum(1 for e in self.errors if '429' in e.get('error', ''))

        final_msg = (f"Scraping complete! Success: {self.success_count:,} | "
                     f"Failed: {self.failed_count:,} | "
                     f"Rate Limited: {rate_limit_errors:,} | "
                     f"Time: {elapsed/60:.1f} minutes | "
                     f"Rate: {total/elapsed:.1f} products/second")

        print(f"\n{'='*70}")
        print(f"Scraping complete!")
        print(f"  Success: {self.success_count:,}")
        print(f"  Failed: {self.failed_count:,}")
        if rate_limit_errors > 0:
            print(f"  Rate Limited (429): {rate_limit_errors:,}")
        print(f"  Time: {elapsed/60:.1f} minutes")
        print(f"  Rate: {total/elapsed:.1f} products/second")
        print(f"{'='*70}")
        print(f"\n{self.get_proxy_stats()}")
        print(f"{'='*70}\n")
        self.logger.info(final_msg)
        self.logger.info(f"Final Proxy Stats - Total Requests: {self.total_requests:,}, "
                        f"Unique IPs Used: {len(self.proxy_ips_seen):,}")

    def save_results(self):
        """Save scraped data to files"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Save products as JSON
        json_file = self.output_dir / f"products_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.products, f, indent=2, ensure_ascii=False)
        msg = f"Saved JSON: {json_file} ({len(self.products):,} products)"
        print(f"✅ {msg}")
        self.logger.info(msg)

        # Save products as CSV
        if self.products:
            csv_file = self.output_dir / f"products_{timestamp}.csv"
            with open(csv_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'url', 'title', 'sku', 'price', 'availability', 'description',
                    'category', 'brand', 'scraped_at'
                ])
                writer.writeheader()
                for product in self.products:
                    row = {k: v for k, v in product.items() if k not in ['specifications', 'images']}
                    writer.writerow(row)
            msg = f"Saved CSV: {csv_file}"
            print(f"✅ {msg}")
            self.logger.info(msg)

        # Save failed URLs
        if self.failed_urls:
            failed_file = self.output_dir / f"failed_urls_{timestamp}.txt"
            with open(failed_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(self.failed_urls))
            msg = f"Failed URLs: {failed_file} ({len(self.failed_urls):,} URLs)"
            print(f"⚠️  {msg}")
            self.logger.warning(msg)

        # Save proxy statistics
        stats_file = self.output_dir / f"proxy_stats_{timestamp}.json"
        proxy_stats = {
            'total_requests': self.total_requests,
            'unique_ips': len(self.proxy_ips_seen),
            'proxy_ips_used': list(self.proxy_ips_seen),
            'requests_by_status': self.requests_by_status,
            'success_rate': (self.requests_by_status['success'] / self.total_requests * 100) if self.total_requests > 0 else 0,
            'timestamp': timestamp
        }
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(proxy_stats, f, indent=2)
        msg = f"Saved proxy stats: {stats_file}"
        print(f"📊 {msg}")
        self.logger.info(msg)

        self.logger.info(f"All results saved. Log file: {self.log_file}")


def main():
    parser = argparse.ArgumentParser(description='Scrape MRO Supply products with rotating residential proxy')
    parser.add_argument('--url-file', default='all_product_urls_20251215_230531.txt',
                        help='File containing product URLs')
    parser.add_argument('--workers', type=int, default=20,
                        help='Number of concurrent workers (default: 20)')
    parser.add_argument('--delay', type=float, default=0.3,
                        help='Delay between requests in seconds (default: 0.3)')
    parser.add_argument('--target', type=int, default=None,
                        help='Target number of products to scrape (default: all)')
    parser.add_argument('--output-dir', default='scraped_rotating_residential',
                        help='Output directory (default: scraped_rotating_residential)')
    parser.add_argument('--resume', action='store_true',
                        help='Resume from checkpoint (skip already scraped URLs)')
    parser.add_argument('--retry-errors', action='store_true',
                        help='Retry previously failed URLs from errors.jsonl')
    parser.add_argument('--rate-limit-threshold', type=int, default=10,
                        help='Number of 429 errors before pausing (default: 10)')
    parser.add_argument('--cooldown-minutes', type=int, default=15,
                        help='Minutes to wait when rate limited (default: 15)')

    args = parser.parse_args()

    # Initialize scraper with rotating residential proxy
    import os
    scraper = RotatingResidentialScraper(
        proxy_host=os.getenv('PROXY_HOST', 'p.webshare.io'),
        proxy_port=int(os.getenv('PROXY_PORT', '10000')),
        proxy_user=os.getenv('PROXY_USER', 'your_username'),
        proxy_pass=os.getenv('PROXY_PASS', 'your_password'),
        output_dir=args.output_dir,
        workers=args.workers,
        delay=args.delay,
        rate_limit_threshold=args.rate_limit_threshold,
        cooldown_minutes=args.cooldown_minutes
    )

    # Resume from checkpoint if requested
    if args.resume:
        print("\n🔄 Resume mode enabled")
        scraper.load_checkpoint()

    # Determine which URLs to scrape
    urls = []

    if args.retry_errors:
        print("\n🔁 Retry errors mode enabled")
        urls = scraper.load_failed_urls()
        if not urls:
            print("ℹ️  No failed URLs to retry")

        # Clear old error file to start fresh for this retry session
        if scraper.error_file.exists():
            scraper.error_file.unlink()
            print("🗑️  Cleared old error file")

    else:
        # Load URLs from file
        print(f"Loading URLs from {args.url_file}...")
        with open(args.url_file, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
        print(f"✅ Loaded {len(urls):,} URLs")
        scraper.logger.info(f"Loaded {len(urls):,} URLs from {args.url_file}")

    # Scrape
    if urls:
        scraper.scrape_urls(urls, target=args.target)

        # Save results
        scraper.save_results()

        print("\n✅ All done!")
        scraper.logger.info("Scraping session completed")
    else:
        print("\n⚠️  No URLs to scrape")
        scraper.logger.warning("No URLs to scrape")


if __name__ == "__main__":
    main()
