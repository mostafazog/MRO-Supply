#!/usr/bin/env python3
"""
Aggregate results from all GitHub Actions workers
"""

import json
import glob
from pathlib import Path
from datetime import datetime


def aggregate_results(artifacts_dir: str):
    """Aggregate all worker results"""
    print("="*70)
    print("AGGREGATING RESULTS")
    print("="*70)

    all_products = []
    all_errors = []

    # Find all worker result files
    product_files = glob.glob(f"{artifacts_dir}/**/worker_*_products.json", recursive=True)
    error_files = glob.glob(f"{artifacts_dir}/**/worker_*_errors.json", recursive=True)

    print(f"\nFound {len(product_files)} product files")
    print(f"Found {len(error_files)} error files")
    print()

    # Aggregate products
    for file in product_files:
        print(f"📄 Reading: {file}")
        try:
            with open(file, 'r') as f:
                products = json.load(f)
                all_products.extend(products)
                print(f"   ✅ {len(products)} products")
        except Exception as e:
            print(f"   ❌ Error reading file: {e}")

    # Aggregate errors
    for file in error_files:
        try:
            with open(file, 'r') as f:
                errors = json.load(f)
                all_errors.extend(errors)
        except Exception as e:
            print(f"   ❌ Error reading errors file: {e}")

    # Remove duplicates (by URL)
    unique_products = {}
    for product in all_products:
        url = product.get('url')
        if url:
            unique_products[url] = product

    all_products = list(unique_products.values())

    # Save aggregated results
    output_file = 'raptor_products_final.json'
    with open(output_file, 'w') as f:
        json.dump(all_products, f, indent=2)

    # Create summary
    total_attempted = len(all_products) + len(all_errors)
    success_rate = (len(all_products) / max(total_attempted, 1)) * 100

    summary = {
        'timestamp': datetime.now().isoformat(),
        'total_products': len(all_products),
        'successful': len(all_products),
        'failed': len(all_errors),
        'success_rate': success_rate,
        'unique_products': len(all_products)
    }

    summary_file = 'raptor_scraping_summary.json'
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)

    # Print summary
    print()
    print("="*70)
    print("✅ AGGREGATION COMPLETE")
    print("="*70)
    print(f"Total products: {len(all_products):,}")
    print(f"Failed: {len(all_errors):,}")
    print(f"Success rate: {success_rate:.1f}%")
    print()
    print(f"Saved to:")
    print(f"  - {output_file} ({len(all_products):,} products)")
    print(f"  - {summary_file}")
    print("="*70)


if __name__ == '__main__':
    import sys

    artifacts_dir = sys.argv[1] if len(sys.argv) > 1 else 'artifacts/'
    aggregate_results(artifacts_dir)
