#!/usr/bin/env python3
"""
Raptor Supplies Sitemap Scraper
Discovers and extracts all product URLs from sitemaps
"""

import requests
import time
import json
import re
import gzip
from typing import List, Dict, Set
from pathlib import Path
from datetime import datetime
from xml.etree import ElementTree as ET
from urllib.parse import urljoin, urlparse
import logging

# Setup logging
Path("./logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('./logs/raptorsupplies_sitemap.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class RaptorSuppliesSitemapScraper:
    """
    Discovers and extracts product URLs from sitemaps
    """

    def __init__(self, base_url: str = "https://www.raptorsupplies.com"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        })

        self.product_urls = set()
        self.sitemap_urls = set()

        # Common sitemap locations
        self.sitemap_locations = [
            '/sitemap.xml',
            '/sitemap_index.xml',
            '/sitemap-index.xml',
            '/sitemaps/sitemap.xml',
            '/product-sitemap.xml',
            '/products-sitemap.xml',
            '/sitemap_products.xml',
            '/sitemap/products.xml',
            '/sitemap_products_1.xml',
            '/robots.txt'  # Check robots.txt for sitemap location
        ]

    def fetch_url(self, url: str, is_xml: bool = True) -> str:
        """Fetch URL content with error handling"""
        try:
            logger.info(f"🌐 Fetching: {url}")

            response = self.session.get(url, timeout=30)

            if response.status_code == 200:
                logger.info(f"   ✅ Success (200)")

                # Handle gzipped content
                if url.endswith('.gz'):
                    try:
                        content = gzip.decompress(response.content).decode('utf-8')
                        return content
                    except:
                        pass

                return response.text
            elif response.status_code == 404:
                logger.info(f"   ⏭️  Not found (404)")
                return None
            elif response.status_code == 403:
                logger.warning(f"   ⚠️  Forbidden (403)")
                return None
            else:
                logger.warning(f"   ⚠️  HTTP {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"   ❌ Error: {e}")
            return None

    def find_sitemaps_from_robots(self) -> List[str]:
        """Extract sitemap URLs from robots.txt"""
        robots_url = urljoin(self.base_url, '/robots.txt')
        content = self.fetch_url(robots_url, is_xml=False)

        if not content:
            return []

        # Extract sitemap URLs
        sitemap_urls = []
        for line in content.split('\n'):
            line = line.strip()
            if line.lower().startswith('sitemap:'):
                sitemap_url = line.split(':', 1)[1].strip()
                sitemap_urls.append(sitemap_url)
                logger.info(f"   📋 Found sitemap in robots.txt: {sitemap_url}")

        return sitemap_urls

    def parse_sitemap_index(self, xml_content: str) -> List[str]:
        """Parse sitemap index and return list of sitemap URLs"""
        try:
            root = ET.fromstring(xml_content)

            # Handle namespaces
            namespaces = {
                'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'
            }

            sitemap_urls = []

            # Try with namespace
            for sitemap in root.findall('.//sm:sitemap/sm:loc', namespaces):
                url = sitemap.text.strip()
                sitemap_urls.append(url)
                logger.info(f"   📄 Found sitemap: {url}")

            # Try without namespace (some sites don't use it properly)
            if not sitemap_urls:
                for sitemap in root.findall('.//sitemap/loc'):
                    url = sitemap.text.strip()
                    sitemap_urls.append(url)
                    logger.info(f"   📄 Found sitemap: {url}")

            return sitemap_urls

        except Exception as e:
            logger.error(f"   ❌ Error parsing sitemap index: {e}")
            return []

    def parse_sitemap(self, xml_content: str) -> List[Dict]:
        """Parse sitemap and extract URLs"""
        try:
            root = ET.fromstring(xml_content)

            # Handle namespaces
            namespaces = {
                'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'
            }

            urls = []

            # Try with namespace
            for url_elem in root.findall('.//sm:url', namespaces):
                loc = url_elem.find('sm:loc', namespaces)
                lastmod = url_elem.find('sm:lastmod', namespaces)
                priority = url_elem.find('sm:priority', namespaces)

                if loc is not None:
                    url_data = {
                        'url': loc.text.strip(),
                        'lastmod': lastmod.text.strip() if lastmod is not None else None,
                        'priority': priority.text.strip() if priority is not None else None
                    }
                    urls.append(url_data)

            # Try without namespace
            if not urls:
                for url_elem in root.findall('.//url'):
                    loc = url_elem.find('loc')
                    lastmod = url_elem.find('lastmod')
                    priority = url_elem.find('priority')

                    if loc is not None:
                        url_data = {
                            'url': loc.text.strip(),
                            'lastmod': lastmod.text.strip() if lastmod is not None else None,
                            'priority': priority.text.strip() if priority is not None else None
                        }
                        urls.append(url_data)

            return urls

        except Exception as e:
            logger.error(f"   ❌ Error parsing sitemap: {e}")
            return []

    def is_product_url(self, url: str) -> bool:
        """Determine if URL is a product page"""
        url_lower = url.lower()

        # Common product URL patterns
        product_patterns = [
            '/product/',
            '/products/',
            '/item/',
            '/items/',
            '/p/',
            '/catalog/',
        ]

        # Exclusion patterns (not product pages)
        exclusion_patterns = [
            '/blog/',
            '/category/',
            '/categories/',
            '/collection/',
            '/collections/',
            '/page/',
            '/pages/',
            '/search',
            '/cart',
            '/checkout',
            '/account',
            '/login',
            '/register',
        ]

        # Check exclusions first
        for pattern in exclusion_patterns:
            if pattern in url_lower:
                return False

        # Check if it matches product patterns
        for pattern in product_patterns:
            if pattern in url_lower:
                return True

        return False

    def discover_sitemaps(self) -> List[str]:
        """Discover all sitemap URLs"""
        logger.info("="*70)
        logger.info("DISCOVERING SITEMAPS")
        logger.info("="*70)

        all_sitemaps = []

        # 1. Check robots.txt
        logger.info("\n📋 Step 1: Checking robots.txt...")
        robots_sitemaps = self.find_sitemaps_from_robots()
        all_sitemaps.extend(robots_sitemaps)

        # 2. Try common sitemap locations
        logger.info("\n📋 Step 2: Trying common sitemap locations...")
        for location in self.sitemap_locations:
            if location == '/robots.txt':
                continue  # Already checked

            url = urljoin(self.base_url, location)
            if url in all_sitemaps:
                continue

            content = self.fetch_url(url)
            if content:
                all_sitemaps.append(url)

            time.sleep(1)  # Be polite

        logger.info(f"\n✅ Found {len(all_sitemaps)} sitemap(s)")
        return all_sitemaps

    def process_sitemap(self, sitemap_url: str, depth: int = 0) -> Set[str]:
        """Process a sitemap (may be index or regular sitemap)"""
        indent = "  " * depth
        logger.info(f"\n{indent}📄 Processing: {sitemap_url}")

        product_urls = set()

        # Fetch sitemap
        content = self.fetch_url(sitemap_url)
        if not content:
            return product_urls

        # Check if it's a sitemap index or regular sitemap
        if '<sitemapindex' in content or '<sitemap>' in content:
            logger.info(f"{indent}   📑 Sitemap Index detected")
            child_sitemaps = self.parse_sitemap_index(content)

            logger.info(f"{indent}   Found {len(child_sitemaps)} child sitemaps")

            # Process each child sitemap
            for child_url in child_sitemaps:
                if depth < 3:  # Prevent infinite recursion
                    child_products = self.process_sitemap(child_url, depth + 1)
                    product_urls.update(child_products)
                    time.sleep(1)  # Be polite
        else:
            logger.info(f"{indent}   📄 Regular sitemap")
            urls = self.parse_sitemap(content)
            logger.info(f"{indent}   Found {len(urls)} URLs")

            # Filter for product URLs
            for url_data in urls:
                url = url_data['url']
                if self.is_product_url(url):
                    product_urls.add(url)

            logger.info(f"{indent}   ✅ Found {len(product_urls)} product URLs")

        return product_urls

    def scrape_all_sitemaps(self) -> List[str]:
        """Main function to scrape all product URLs from sitemaps"""
        logger.info("="*70)
        logger.info("RAPTOR SUPPLIES SITEMAP SCRAPER")
        logger.info("="*70)

        # Discover sitemaps
        sitemap_urls = self.discover_sitemaps()

        if not sitemap_urls:
            logger.error("\n❌ No sitemaps found!")
            logger.info("\nTips:")
            logger.info("1. Check if the site has a sitemap")
            logger.info("2. Try manually visiting: https://www.raptorsupplies.com/sitemap.xml")
            logger.info("3. The site may block automated requests (403)")
            return []

        # Process each sitemap
        logger.info("\n" + "="*70)
        logger.info("EXTRACTING PRODUCT URLS")
        logger.info("="*70)

        all_product_urls = set()

        for sitemap_url in sitemap_urls:
            product_urls = self.process_sitemap(sitemap_url)
            all_product_urls.update(product_urls)
            logger.info(f"\n📊 Running total: {len(all_product_urls)} product URLs")
            time.sleep(2)  # Be polite between sitemaps

        # Convert to sorted list
        product_urls_list = sorted(list(all_product_urls))

        # Summary
        logger.info("\n" + "="*70)
        logger.info("SITEMAP SCRAPING COMPLETE")
        logger.info("="*70)
        logger.info(f"✅ Total product URLs found: {len(product_urls_list):,}")
        logger.info("="*70)

        return product_urls_list

    def save_results(self, product_urls: List[str], output_file: str = "raptorsupplies_urls.json"):
        """Save product URLs to file"""
        output_path = Path(output_file)

        data = {
            'source': self.base_url,
            'scraped_at': datetime.now().isoformat(),
            'total_products': len(product_urls),
            'product_urls': product_urls
        }

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"\n💾 Saved {len(product_urls):,} URLs to: {output_path}")

        # Also save as simple text file
        txt_path = output_path.with_suffix('.txt')
        with open(txt_path, 'w') as f:
            for url in product_urls:
                f.write(url + '\n')

        logger.info(f"💾 Saved URLs to: {txt_path}")

        # Save summary
        summary = {
            'total_products': len(product_urls),
            'scraped_at': datetime.now().isoformat(),
            'source': self.base_url,
            'sample_urls': product_urls[:10] if product_urls else []
        }

        summary_path = Path('raptorsupplies_sitemap_summary.json')
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)

        logger.info(f"💾 Saved summary to: {summary_path}")


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Raptor Supplies Sitemap Scraper')
    parser.add_argument('--url', type=str, default='https://www.raptorsupplies.com',
                       help='Base URL (default: https://www.raptorsupplies.com)')
    parser.add_argument('--output', type=str, default='raptorsupplies_urls.json',
                       help='Output file (default: raptorsupplies_urls.json)')

    args = parser.parse_args()

    # Create scraper
    scraper = RaptorSuppliesSitemapScraper(base_url=args.url)

    try:
        # Scrape sitemaps
        product_urls = scraper.scrape_all_sitemaps()

        if product_urls:
            # Save results
            scraper.save_results(product_urls, output_file=args.output)

            # Print sample URLs
            print("\n" + "="*70)
            print("SAMPLE PRODUCT URLS")
            print("="*70)
            for i, url in enumerate(product_urls[:10], 1):
                print(f"{i}. {url}")

            if len(product_urls) > 10:
                print(f"... and {len(product_urls) - 10:,} more")
            print("="*70)

            return 0
        else:
            logger.error("\n❌ No product URLs found")
            return 1

    except KeyboardInterrupt:
        logger.info("\n\n⏸️  Interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        return 1


if __name__ == '__main__':
    exit(main())
