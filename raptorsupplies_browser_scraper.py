#!/usr/bin/env python3
"""
Raptor Supplies Browser-Based Scraper
Uses Selenium with undetected-chromedriver to bypass Cloudflare protection
"""

import json
import time
import re
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime
import logging

# Setup logging
Path("./logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('./logs/raptorsupplies_browser.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class RaptorSuppliesBrowserScraper:
    """
    Browser-based scraper for Cloudflare-protected sites
    """

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None
        self.product_urls = set()

    def init_driver(self):
        """Initialize undetected Chrome driver"""
        try:
            import undetected_chromedriver as uc
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC

            logger.info("🌐 Initializing browser (this may take a moment)...")

            options = uc.ChromeOptions()

            if self.headless:
                options.add_argument('--headless=new')

            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--window-size=1920,1080')

            self.driver = uc.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, 20)

            logger.info("✅ Browser initialized successfully")
            return True

        except ImportError:
            logger.error("❌ undetected-chromedriver not installed!")
            logger.info("\nInstall it with:")
            logger.info("  pip3 install undetected-chromedriver selenium")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to initialize browser: {e}")
            return False

    def wait_for_cloudflare(self, timeout: int = 30):
        """Wait for Cloudflare challenge to complete"""
        logger.info("⏳ Waiting for Cloudflare challenge...")
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # Check if still in Cloudflare challenge
                page_source = self.driver.page_source.lower()

                if 'just a moment' in page_source or 'checking your browser' in page_source:
                    logger.debug("   Still in challenge...")
                    time.sleep(2)
                    continue

                # Check if we got through
                if 'cloudflare' not in page_source or len(page_source) > 10000:
                    logger.info("✅ Cloudflare challenge passed!")
                    return True

                time.sleep(2)

            except Exception as e:
                logger.error(f"Error waiting for Cloudflare: {e}")
                time.sleep(2)

        logger.warning("⚠️ Cloudflare challenge timeout")
        return False

    def get_page(self, url: str, wait_time: int = 5) -> bool:
        """Navigate to a page and wait for Cloudflare"""
        try:
            logger.info(f"🌐 Loading: {url}")
            self.driver.get(url)

            # Wait for Cloudflare
            if not self.wait_for_cloudflare():
                return False

            # Additional wait for page content
            time.sleep(wait_time)

            return True

        except Exception as e:
            logger.error(f"❌ Error loading page: {e}")
            return False

    def find_sitemap_in_page(self) -> List[str]:
        """Try to find sitemap links in the current page"""
        sitemaps = []

        try:
            # Check page source for sitemap references
            page_source = self.driver.page_source

            # Find sitemap URLs in the HTML
            sitemap_patterns = [
                r'href="([^"]*sitemap[^"]*\.xml)"',
                r"href='([^']*sitemap[^']*\.xml)'",
                r'<loc>([^<]*sitemap[^<]*\.xml)</loc>',
            ]

            for pattern in sitemap_patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                sitemaps.extend(matches)

            # Try direct sitemap URLs
            base_url = "https://www.raptorsupplies.com"
            direct_sitemaps = [
                f"{base_url}/sitemap.xml",
                f"{base_url}/sitemap_index.xml",
                f"{base_url}/products.xml",
            ]

            for sitemap_url in direct_sitemaps:
                if self.get_page(sitemap_url, wait_time=3):
                    if 'xml' in self.driver.page_source.lower():
                        sitemaps.append(sitemap_url)

        except Exception as e:
            logger.error(f"Error finding sitemaps: {e}")

        return list(set(sitemaps))

    def extract_product_urls_from_sitemap(self, sitemap_url: str) -> List[str]:
        """Extract product URLs from a sitemap"""
        products = []

        try:
            if not self.get_page(sitemap_url, wait_time=3):
                return products

            # Get page source (XML)
            xml_content = self.driver.page_source

            # Extract URLs using regex (simpler than XML parsing in browser context)
            url_pattern = r'<loc>(https://www\.raptorsupplies\.com/[^<]+)</loc>'
            urls = re.findall(url_pattern, xml_content)

            # Filter for product URLs
            for url in urls:
                url_lower = url.lower()
                if any(pattern in url_lower for pattern in ['/product', '/item', '/p/']):
                    if not any(exclude in url_lower for exclude in ['/category', '/collection', '/blog', '/page']):
                        products.append(url)

            logger.info(f"   Found {len(products)} product URLs")

        except Exception as e:
            logger.error(f"Error extracting from sitemap: {e}")

        return products

    def scrape_sitemaps(self) -> List[str]:
        """Main method to scrape all product URLs"""
        logger.info("="*70)
        logger.info("RAPTOR SUPPLIES BROWSER SCRAPER")
        logger.info("Bypassing Cloudflare protection...")
        logger.info("="*70)

        if not self.init_driver():
            return []

        try:
            # Step 1: Try to access homepage
            logger.info("\n📋 Step 1: Accessing homepage...")
            if not self.get_page("https://www.raptorsupplies.com"):
                logger.error("❌ Failed to bypass Cloudflare on homepage")
                return []

            # Step 2: Try robots.txt
            logger.info("\n📋 Step 2: Checking robots.txt...")
            if self.get_page("https://www.raptorsupplies.com/robots.txt", wait_time=2):
                page_text = self.driver.find_element("tag name", "body").text
                logger.info(f"\n{page_text[:500]}")  # Show first 500 chars

                # Extract sitemap URLs from robots.txt
                sitemap_pattern = r'Sitemap:\s*(https?://[^\s]+)'
                sitemaps = re.findall(sitemap_pattern, page_text, re.IGNORECASE)

                if sitemaps:
                    logger.info(f"\n✅ Found {len(sitemaps)} sitemap(s) in robots.txt:")
                    for sitemap in sitemaps:
                        logger.info(f"   - {sitemap}")

                    # Step 3: Process each sitemap
                    logger.info("\n📋 Step 3: Extracting product URLs from sitemaps...")

                    all_products = set()
                    for sitemap_url in sitemaps:
                        logger.info(f"\n📄 Processing: {sitemap_url}")
                        products = self.extract_product_urls_from_sitemap(sitemap_url)
                        all_products.update(products)
                        logger.info(f"   Total so far: {len(all_products)}")
                        time.sleep(2)  # Be polite

                    return sorted(list(all_products))

            # Step 4: Try common sitemap locations
            logger.info("\n📋 Step 4: Trying common sitemap locations...")
            common_sitemaps = [
                "https://www.raptorsupplies.com/sitemap.xml",
                "https://www.raptorsupplies.com/sitemap_index.xml",
                "https://www.raptorsupplies.com/products-sitemap.xml",
            ]

            all_products = set()
            for sitemap_url in common_sitemaps:
                logger.info(f"\n📄 Trying: {sitemap_url}")
                products = self.extract_product_urls_from_sitemap(sitemap_url)
                if products:
                    all_products.update(products)
                    logger.info(f"   Total so far: {len(all_products)}")
                time.sleep(2)

            if all_products:
                return sorted(list(all_products))

            logger.error("\n❌ No product URLs found")
            return []

        except Exception as e:
            logger.error(f"\n❌ Error during scraping: {e}")
            return []

        finally:
            if self.driver:
                logger.info("\n🔒 Closing browser...")
                self.driver.quit()

    def save_results(self, product_urls: List[str], output_file: str = "raptorsupplies_urls.json"):
        """Save product URLs to file"""
        if not product_urls:
            logger.warning("No URLs to save")
            return

        output_path = Path(output_file)

        data = {
            'source': 'https://www.raptorsupplies.com',
            'scraped_at': datetime.now().isoformat(),
            'total_products': len(product_urls),
            'product_urls': product_urls
        }

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"\n💾 Saved {len(product_urls):,} URLs to: {output_path}")

        # Also save as text file
        txt_path = output_path.with_suffix('.txt')
        with open(txt_path, 'w') as f:
            for url in product_urls:
                f.write(url + '\n')

        logger.info(f"💾 Saved URLs to: {txt_path}")


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Raptor Supplies Browser-Based Sitemap Scraper')
    parser.add_argument('--no-headless', action='store_true',
                       help='Show browser window (for debugging)')
    parser.add_argument('--output', type=str, default='raptorsupplies_urls.json',
                       help='Output file')

    args = parser.parse_args()

    # Check dependencies
    try:
        import undetected_chromedriver
        import selenium
    except ImportError:
        print("\n❌ Missing dependencies!")
        print("\nInstall required packages:")
        print("  pip3 install undetected-chromedriver selenium")
        print("\nNote: You also need Chrome/Chromium installed on your system")
        return 1

    # Create scraper
    scraper = RaptorSuppliesBrowserScraper(headless=not args.no_headless)

    try:
        # Scrape sitemaps
        product_urls = scraper.scrape_sitemaps()

        if product_urls:
            # Save results
            scraper.save_results(product_urls, output_file=args.output)

            # Print summary
            print("\n" + "="*70)
            print("SCRAPING COMPLETE")
            print("="*70)
            print(f"Total product URLs: {len(product_urls):,}")
            print("\nSample URLs:")
            for i, url in enumerate(product_urls[:10], 1):
                print(f"{i}. {url}")
            if len(product_urls) > 10:
                print(f"... and {len(product_urls) - 10:,} more")
            print("="*70)

            return 0
        else:
            print("\n❌ No product URLs found")
            return 1

    except KeyboardInterrupt:
        print("\n\n⏸️  Interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        return 1


if __name__ == '__main__':
    exit(main())
