"""
Aggregate variant data from all workers
"""

import json
import os
import sys
from datetime import datetime

def aggregate_variants(artifacts_dir='artifacts'):
    """Aggregate product variants from all worker artifacts"""
    print("=" * 80)
    print("📦 AGGREGATING PRODUCT VARIANTS")
    print("=" * 80)

    all_products = []
    total_collections = 0
    workers_processed = 0
    total_with_sku = 0
    total_with_price = 0

    # Find all worker result files
    for root, dirs, files in os.walk(artifacts_dir):
        for file in files:
            if file.endswith('_products.json') and file.startswith('worker_'):
                filepath = os.path.join(root, file)
                print(f"\n📄 Processing: {filepath}")

                try:
                    with open(filepath, 'r') as f:
                        products = json.load(f)

                    worker_id = products[0]['worker_id'] if products else '?'
                    collections = len(set(p.get('collection_url', p.get('url')) for p in products))

                    # Count products with data
                    with_sku = sum(1 for p in products if p.get('sku'))
                    with_price = sum(1 for p in products if p.get('price'))

                    print(f"   Worker {worker_id}: {len(products)} variants from {collections} collections")
                    print(f"   - With SKU: {with_sku}")
                    print(f"   - With Price: {with_price}")

                    all_products.extend(products)
                    total_collections += collections
                    workers_processed += 1
                    total_with_sku += with_sku
                    total_with_price += with_price

                except Exception as e:
                    print(f"   ❌ Error: {str(e)}")

    # Create final output
    print(f"\n💾 Creating final aggregated file...")

    # Create summary statistics
    summary = {
        "scraped_at": datetime.now().isoformat(),
        "workers": workers_processed,
        "total_collections": total_collections,
        "total_variants": len(all_products),
        "variants_with_sku": total_with_sku,
        "variants_with_price": total_with_price,
        "sku_percentage": round(total_with_sku / len(all_products) * 100, 2) if all_products else 0,
        "price_percentage": round(total_with_price / len(all_products) * 100, 2) if all_products else 0
    }

    # Save all products
    output_file = "raptor_variants_final.json"
    with open(output_file, 'w') as f:
        json.dump(all_products, f, indent=2)

    # Save summary
    summary_file = "raptor_variants_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)

    # Create sample file (first 100 products)
    sample_file = "raptor_variants_sample.json"
    with open(sample_file, 'w') as f:
        json.dump(all_products[:100], f, indent=2)

    # Print summary
    print("\n" + "=" * 80)
    print("✨ AGGREGATION COMPLETE!")
    print("=" * 80)
    print(f"👷 Workers processed: {workers_processed}")
    print(f"📦 Collections processed: {total_collections}")
    print(f"🎯 Total variants extracted: {len(all_products):,}")
    print(f"")
    print(f"Data Quality:")
    print(f"  - Variants with SKU: {total_with_sku:,} ({summary['sku_percentage']}%)")
    print(f"  - Variants with Price: {total_with_price:,} ({summary['price_percentage']}%)")
    print(f"")
    print(f"💾 Files created:")
    print(f"  - {output_file} - All {len(all_products):,} variants")
    print(f"  - {summary_file} - Statistics")
    print(f"  - {sample_file} - Sample of 100 variants")

    return len(all_products)


if __name__ == "__main__":
    artifacts_dir = sys.argv[1] if len(sys.argv) > 1 else 'artifacts'
    count = aggregate_variants(artifacts_dir)
    sys.exit(0 if count > 0 else 1)
