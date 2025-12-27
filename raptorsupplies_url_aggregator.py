"""
Aggregate individual product URLs from all workers
"""

import json
import os
import sys
from datetime import datetime

def aggregate_urls(artifacts_dir='artifacts'):
    """Aggregate URLs from all worker artifacts"""
    print("=" * 80)
    print("📦 AGGREGATING INDIVIDUAL PRODUCT URLs")
    print("=" * 80)

    all_urls = set()
    total_collections = 0
    workers_processed = 0

    # Find all worker result files
    for root, dirs, files in os.walk(artifacts_dir):
        for file in files:
            if file.endswith('_individual_urls.json'):
                filepath = os.path.join(root, file)
                print(f"\n📄 Processing: {filepath}")

                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)

                    worker_id = data.get('worker_id', '?')
                    urls = data.get('urls', [])
                    collections = data.get('collections_processed', 0)

                    print(f"   Worker {worker_id}: {len(urls)} URLs from {collections} collections")

                    all_urls.update(urls)
                    total_collections += collections
                    workers_processed += 1

                except Exception as e:
                    print(f"   ❌ Error: {str(e)}")

    # Create final output
    print(f"\n💾 Creating final aggregated file...")

    output = {
        "extracted_at": datetime.now().isoformat(),
        "workers_processed": workers_processed,
        "total_collections_processed": total_collections,
        "total_individual_urls": len(all_urls),
        "urls": sorted(list(all_urls))
    }

    # Save to file
    output_file = "raptor_individual_products.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    # Save URL-only list for easy use
    urls_only_file = "raptor_individual_products_urls.txt"
    with open(urls_only_file, 'w') as f:
        for url in sorted(all_urls):
            f.write(url + '\n')

    # Create summary
    summary = {
        "timestamp": datetime.now().isoformat(),
        "workers": workers_processed,
        "collections_processed": total_collections,
        "individual_urls_found": len(all_urls),
        "output_files": [output_file, urls_only_file]
    }

    with open("url_extraction_summary.json", 'w') as f:
        json.dump(summary, f, indent=2)

    # Print summary
    print("\n" + "=" * 80)
    print("✨ AGGREGATION COMPLETE!")
    print("=" * 80)
    print(f"👷 Workers processed: {workers_processed}")
    print(f"📦 Collections processed: {total_collections}")
    print(f"🎯 Total individual URLs found: {len(all_urls):,}")
    print(f"💾 Saved to: {output_file}")
    print(f"📄 Plain text list: {urls_only_file}")

    return len(all_urls)


if __name__ == "__main__":
    artifacts_dir = sys.argv[1] if len(sys.argv) > 1 else 'artifacts'
    count = aggregate_urls(artifacts_dir)
    sys.exit(0 if count > 0 else 1)
