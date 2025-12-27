#!/usr/bin/env python3
"""
Parse locally downloaded sitemap XML files
Use this after manually downloading sitemaps from your browser
"""

import xml.etree.ElementTree as ET
import json
import glob
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def parse_sitemap(xml_file):
    """Parse a single sitemap XML file"""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        urls = []

        # Define namespaces
        namespaces = {
            's': 'http://www.sitemaps.org/schemas/sitemap/0.9',
            '': 'http://www.sitemaps.org/schemas/sitemap/0.9'
        }

        # Try with namespace
        for url_elem in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
            loc = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
            if loc is not None:
                url = loc.text
                # Filter for product URLs
                if any(pattern in url.lower() for pattern in ['/product', '/item', '/p/']):
                    if not any(exclude in url.lower() for exclude in ['/category', '/collection', '/blog']):
                        urls.append(url)

        # Try without namespace (some sitemaps don't use it properly)
        if not urls:
            for url_elem in root.findall('.//url'):
                loc = url_elem.find('loc')
                if loc is not None:
                    url = loc.text
                    if any(pattern in url.lower() for pattern in ['/product', '/item', '/p/']):
                        if not any(exclude in url.lower() for exclude in ['/category', '/collection', '/blog']):
                            urls.append(url)

        # Check if it's a sitemap index
        sitemap_urls = []
        for sitemap in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap'):
            loc = sitemap.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
            if loc is not None:
                sitemap_urls.append(loc.text)

        if not sitemap_urls:
            for sitemap in root.findall('.//sitemap'):
                loc = sitemap.find('loc')
                if loc is not None:
                    sitemap_urls.append(loc.text)

        return urls, sitemap_urls

    except Exception as e:
        logger.error(f"Error parsing {xml_file}: {e}")
        return [], []


def main():
    logger.info("="*70)
    logger.info("LOCAL SITEMAP PARSER")
    logger.info("Parse manually downloaded sitemap files")
    logger.info("="*70)
    logger.info("")

    # Find all XML files in current directory
    xml_files = glob.glob('*.xml') + glob.glob('sitemap*.xml')

    if not xml_files:
        logger.info("❌ No XML files found in current directory!")
        logger.info("")
        logger.info("HOW TO USE:")
        logger.info("1. Open your browser (Chrome/Firefox)")
        logger.info("2. Visit: https://www.raptorsupplies.com/robots.txt")
        logger.info("3. Find sitemap URLs (lines starting with 'Sitemap:')")
        logger.info("4. Download each sitemap by visiting the URL")
        logger.info("5. Right-click > Save As > save to this directory")
        logger.info("6. Run this script again")
        logger.info("")
        return

    logger.info(f"📁 Found {len(xml_files)} XML file(s):")
    for f in xml_files:
        logger.info(f"   - {f}")
    logger.info("")

    all_products = set()
    all_sitemaps = set()

    # Parse each file
    for xml_file in xml_files:
        logger.info(f"📄 Parsing: {xml_file}")
        products, sitemaps = parse_sitemap(xml_file)

        if products:
            all_products.update(products)
            logger.info(f"   ✅ Found {len(products)} product URL(s)")

        if sitemaps:
            all_sitemaps.update(sitemaps)
            logger.info(f"   📋 Found {len(sitemaps)} sitemap URL(s)")

        if not products and not sitemaps:
            logger.info("   ⚠️  No products or sitemaps found")

    # If we found sitemap indexes, show them
    if all_sitemaps:
        logger.info("")
        logger.info("="*70)
        logger.info("📋 SITEMAP INDEX FOUND")
        logger.info("="*70)
        logger.info("This file contains references to other sitemaps.")
        logger.info("Download these additional sitemaps:")
        logger.info("")
        for sitemap in sorted(all_sitemaps):
            logger.info(f"   - {sitemap}")
        logger.info("")

    # Save results
    if all_products:
        product_list = sorted(list(all_products))

        # Save as JSON
        output_data = {
            'source': 'Raptor Supplies (manually downloaded)',
            'total_products': len(product_list),
            'product_urls': product_list
        }

        json_file = 'raptorsupplies_urls.json'
        with open(json_file, 'w') as f:
            json.dump(output_data, f, indent=2)

        # Save as text file
        txt_file = 'raptorsupplies_urls.txt'
        with open(txt_file, 'w') as f:
            for url in product_list:
                f.write(url + '\n')

        # Summary
        logger.info("="*70)
        logger.info("✅ PARSING COMPLETE")
        logger.info("="*70)
        logger.info(f"Total products found: {len(product_list):,}")
        logger.info("")
        logger.info("Output files:")
        logger.info(f"   - {json_file} (JSON format)")
        logger.info(f"   - {txt_file} (text format)")
        logger.info("")

        # Show sample URLs
        logger.info("Sample product URLs:")
        for i, url in enumerate(product_list[:10], 1):
            logger.info(f"   {i}. {url}")

        if len(product_list) > 10:
            logger.info(f"   ... and {len(product_list) - 10:,} more")

        logger.info("="*70)

    else:
        logger.info("")
        logger.info("⚠️  No product URLs found in the XML files.")
        logger.info("")
        logger.info("Possible reasons:")
        logger.info("1. Downloaded file is a sitemap index (not actual products)")
        logger.info("2. Product URLs don't match expected patterns")
        logger.info("3. File format is different than expected")
        logger.info("")
        logger.info("Check the XML files manually to see their structure.")


if __name__ == '__main__':
    main()
