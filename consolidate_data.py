#!/usr/bin/env python3
"""
Consolidate all scraped data from GitHub Actions artifacts
Merges JSON files and creates final CSV output
"""

import os
import sys
import json
import csv
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Configuration
GITHUB_DATA_DIR = Path('github_data')
OUTPUT_FILE = Path('consolidated_products.json')
OUTPUT_CSV = Path('consolidated_products.csv')

def consolidate_data():
    """Consolidate all JSON files from GitHub Actions artifacts"""

    if not GITHUB_DATA_DIR.exists():
        print(f"❌ Data directory not found: {GITHUB_DATA_DIR}")
        print("   Run fetch_github_data.py first to download artifacts")
        return

    print("Consolidating data from GitHub Actions artifacts...")
    print(f"Source: {GITHUB_DATA_DIR.absolute()}")

    all_products = {}
    duplicate_count = 0
    error_count = 0
    skipped_errors = 0

    # Find all JSON files (exclude metadata files)
    json_files = [f for f in GITHUB_DATA_DIR.glob('**/*.json') if 'metadata' not in f.name]
    print(f"Found {len(json_files)} JSON files")

    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)

            # Handle different data structures
            if isinstance(data, list):
                products = data
            elif isinstance(data, dict):
                products = data.get('products', data.get('results', []))
                if not products and 'url' in data:
                    # Single product
                    products = [data]
            else:
                continue

            # Add products (SKIP ERRORS!)
            for product in products:
                if isinstance(product, dict):
                    url = product.get('url', '')

                    # Skip products with errors
                    if 'error' in product:
                        skipped_errors += 1
                        continue

                    # Skip products without name (incomplete data)
                    if not product.get('name'):
                        skipped_errors += 1
                        continue

                    if url:
                        if url in all_products:
                            duplicate_count += 1
                        else:
                            all_products[url] = product

        except Exception as e:
            error_count += 1
            print(f"  ⚠️  Error reading {json_file.name}: {e}")

    print(f"\n{'='*60}")
    print(f"✅ Successful products: {len(all_products):,}")
    print(f"⏭️  Duplicates skipped: {duplicate_count:,}")
    print(f"❌ Errors/incomplete skipped: {skipped_errors:,}")
    print(f"⚠️  File read errors: {error_count}")

    if not all_products:
        print("❌ No products found!")
        return

    # Save consolidated JSON
    print(f"\nSaving consolidated data...")
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(list(all_products.values()), f, indent=2)
    print(f"✓ JSON: {OUTPUT_FILE} ({os.path.getsize(OUTPUT_FILE):,} bytes)")

    # Save as CSV
    print(f"Converting to CSV...")
    products_list = list(all_products.values())

    # Get all possible fields
    all_fields = set()
    for product in products_list:
        all_fields.update(product.keys())

    fieldnames = sorted(all_fields)

    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(products_list)

    print(f"✓ CSV: {OUTPUT_CSV} ({os.path.getsize(OUTPUT_CSV):,} bytes)")

    # Statistics
    print(f"\n{'='*60}")
    print("Statistics:")
    print(f"  Total unique products: {len(all_products):,}")
    print(f"  Fields per product: {len(fieldnames)}")

    # Show sample fields
    print(f"\nFields: {', '.join(list(fieldnames)[:10])}")
    if len(fieldnames) > 10:
        print(f"        ... and {len(fieldnames) - 10} more")

    # Show sample product
    if products_list:
        sample = products_list[0]
        print(f"\nSample product:")
        print(f"  Title: {sample.get('title', 'N/A')}")
        print(f"  SKU: {sample.get('sku', 'N/A')}")
        print(f"  Price: {sample.get('price', 'N/A')}")
        print(f"  URL: {sample.get('url', 'N/A')}")

    print(f"\n✅ Done! Data saved to:")
    print(f"   {OUTPUT_FILE.absolute()}")
    print(f"   {OUTPUT_CSV.absolute()}")

if __name__ == '__main__':
    try:
        consolidate_data()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
