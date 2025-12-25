#!/usr/bin/env python3
"""
Launch Distributed Image-Filtered Scraper via GitHub Actions
Scrapes 1.5M products using 100+ parallel workers, filtering only products with images
"""

import json
import requests
import time
import os
from datetime import datetime

# Configuration
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
if not GITHUB_TOKEN:
    print("❌ ERROR: GITHUB_TOKEN environment variable not set!")
    print("Set it with: export GITHUB_TOKEN='your_token_here'")
    exit(1)

REPO = "mostafazog/MRO-Supply"
WORKFLOW_FILE = "distributed-scrape-image-filter.yml"

# Scraping configuration
TOTAL_PRODUCTS = 1_508_714
BATCH_SIZE = 100
GITHUB_WORKERS = 256  # Maximum allowed by GitHub Actions

print("="*70)
print("DISTRIBUTED IMAGE-FILTERED SCRAPER")
print("GitHub Actions with 100 Parallel Workers")
print("="*70)
print()

def trigger_workflow(total_products=None, batch_size=None, workers=None):
    """Trigger the GitHub Actions workflow"""

    total = total_products or TOTAL_PRODUCTS
    batch = batch_size or BATCH_SIZE
    num_workers = workers or GITHUB_WORKERS

    # Calculate stats
    total_batches = (total + batch - 1) // batch
    batches_per_worker = (total_batches + num_workers - 1) // num_workers

    print(f"📊 Configuration:")
    print(f"   Total products: {total:,}")
    print(f"   Batch size: {batch}")
    print(f"   GitHub workers: {num_workers}")
    print(f"   Total batches: {total_batches:,}")
    print(f"   Batches per worker: ~{batches_per_worker}")
    print()

    # Estimated products with images (based on 13-22% success rate)
    estimated_low = int(total * 0.13)
    estimated_high = int(total * 0.22)
    print(f"📈 Expected results:")
    print(f"   Products with images: {estimated_low:,} - {estimated_high:,}")
    print(f"   Success rate: 13-22%")
    print()

    # Prepare payload
    payload = {
        'ref': 'main',
        'inputs': {
            'total_products': str(total),
            'batch_size': str(batch),
            'github_workers': str(num_workers)
        }
    }

    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }

    print(f"🚀 Triggering workflow...")
    print(f"   Workflow: {WORKFLOW_FILE}")
    print(f"   Repository: {REPO}")
    print()

    try:
        response = requests.post(
            f'https://api.github.com/repos/{REPO}/actions/workflows/{WORKFLOW_FILE}/dispatches',
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code == 204:
            print("✅ SUCCESS! Workflow triggered successfully!")
            print()
            print("="*70)
            print("WHAT HAPPENS NEXT")
            print("="*70)
            print()
            print(f"✅ {num_workers} GitHub Actions workers are starting")
            print(f"✅ Each worker will scrape ~{batches_per_worker * batch:,} products")
            print(f"✅ Only products WITH images will be saved")
            print(f"✅ Results will be automatically aggregated")
            print()
            print("⏱️  Estimated completion time:")
            # Each worker processes ~150 batches, at 0.5s per product = ~75 seconds per batch
            # With 5 parallel requests per batch = ~15 seconds per batch
            # ~150 batches * 15s = ~2250 seconds = ~40 minutes per worker
            print(f"   ~40-60 minutes (all workers run in parallel)")
            print()
            print("📊 Monitor progress:")
            print(f"   https://github.com/{REPO}/actions")
            print()
            print("💾 Results will be saved as artifacts:")
            print("   - consolidated_products_with_images.json (all products)")
            print("   - final_summary.json (statistics)")
            print("   - SCRAPING_REPORT.md (detailed report)")
            print()
            print("="*70)

            return True

        else:
            print(f"❌ FAILED: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def check_workflow_status():
    """Check if workflow is already running"""
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }

    try:
        response = requests.get(
            f'https://api.github.com/repos/{REPO}/actions/workflows/{WORKFLOW_FILE}/runs',
            headers=headers,
            params={'status': 'in_progress', 'per_page': 5},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            running_workflows = [run for run in data['workflow_runs'] if run['status'] in ['queued', 'in_progress']]

            if running_workflows:
                print("⚠️  WARNING: There are already workflows running!")
                print()
                for run in running_workflows:
                    print(f"   Run #{run['run_number']}: {run['status']}")
                    print(f"   Started: {run['created_at']}")
                    print(f"   URL: {run['html_url']}")
                    print()

                answer = input("Do you want to trigger another workflow anyway? (yes/no): ")
                return answer.lower() in ['yes', 'y']

            return True
        else:
            print(f"⚠️  Could not check workflow status (HTTP {response.status_code})")
            return True

    except Exception as e:
        print(f"⚠️  Could not check workflow status: {e}")
        return True

if __name__ == '__main__':
    import sys

    # Check for test mode
    if '--test' in sys.argv:
        print("🧪 TEST MODE: Scraping only 1,000 products with 10 workers")
        print()
        if check_workflow_status():
            trigger_workflow(total_products=1000, batch_size=100, workers=10)
    else:
        print("🚀 FULL MODE: Scraping 1.5M products with 100 workers")
        print()
        if check_workflow_status():
            trigger_workflow()

    print()
    print("💡 TIP: Run with --test flag to test with 1,000 products first")
    print("   python3 launch_distributed_scraper.py --test")
