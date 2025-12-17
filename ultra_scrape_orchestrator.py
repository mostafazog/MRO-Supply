#!/usr/bin/env python3
"""
Ultra-Fast Orchestrator for 100 Azure Functions
Distributes 1.5M products across 100 functions
Completes in 5-10 minutes!
"""

import json
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# Configuration
TOTAL_PRODUCTS = 1_508_714
BATCH_SIZE = 100
TOTAL_BATCHES = (TOTAL_PRODUCTS + BATCH_SIZE - 1) // BATCH_SIZE

print("="*70)
print("ULTRA-FAST SCRAPER - 100 Azure Functions")
print("="*70)
print(f"Total Products: {TOTAL_PRODUCTS:,}")
print(f"Batch Size: {BATCH_SIZE}")
print(f"Total Batches: {TOTAL_BATCHES:,}")
print()

# Load Azure Functions configuration
with open('ultra_config.json', 'r') as f:
    config = json.load(f)

functions = config['functions']
print(f"Loaded {len(functions)} Azure Functions")
print()

# Calculate distribution
batches_per_function = TOTAL_BATCHES // len(functions)
print(f"Distribution: {batches_per_function} batches per function")
print(f"Products per function: {batches_per_function * BATCH_SIZE:,}")
print()

input("Press Enter to start ultra-fast scraping...")

# Distribute batches to functions
function_assignments = []
current_batch = 0

for i, func in enumerate(functions):
    start_batch = current_batch
    end_batch = min(current_batch + batches_per_function, TOTAL_BATCHES)

    # Last function gets remaining batches
    if i == len(functions) - 1:
        end_batch = TOTAL_BATCHES

    function_assignments.append({
        'function': func,
        'start_batch': start_batch,
        'end_batch': end_batch,
        'total_batches': end_batch - start_batch
    })

    current_batch = end_batch

print("="*70)
print("Starting deployment to 100 Azure Functions...")
print("="*70)

def scrape_function_range(assignment):
    """Send batches to a single Azure Function"""
    func = assignment['function']
    start_batch = assignment['start_batch']
    end_batch = assignment['end_batch']

    function_url = f"{func['url']}/api/scrape_range"
    params = {'code': func['key']} if func['key'] != 'pending' else {}

    payload = {
        'start_batch': start_batch,
        'end_batch': end_batch,
        'batch_size': BATCH_SIZE,
        'function_id': func['index']
    }

    try:
        start_time = time.time()

        response = requests.post(
            function_url,
            params=params,
            json=payload,
            timeout=900  # 15 minute timeout
        )

        duration = time.time() - start_time

        if response.status_code == 200:
            result = response.json()
            return {
                'function_id': func['index'],
                'region': func['region'],
                'success': True,
                'batches': result.get('batches_processed', 0),
                'products': result.get('products_scraped', 0),
                'duration': duration
            }
        else:
            return {
                'function_id': func['index'],
                'region': func['region'],
                'success': False,
                'error': f'HTTP {response.status_code}',
                'duration': duration
            }

    except Exception as e:
        return {
            'function_id': func['index'],
            'region': func['region'],
            'success': False,
            'error': str(e),
            'duration': time.time() - start_time
        }

# Execute all functions in parallel
start_time = time.time()
results = []

print(f"\n🚀 Launching {len(function_assignments)} Azure Functions simultaneously...")
print(f"⏱️  Started at: {datetime.now().strftime('%H:%M:%S')}")
print()

with ThreadPoolExecutor(max_workers=100) as executor:
    futures = {
        executor.submit(scrape_function_range, assignment): assignment
        for assignment in function_assignments
    }

    completed = 0
    total_products = 0
    total_batches = 0

    for future in as_completed(futures):
        completed += 1
        result = future.result()
        results.append(result)

        if result['success']:
            total_products += result.get('products', 0)
            total_batches += result.get('batches', 0)
            print(f"✅ [{completed}/{len(functions)}] Function {result['function_id']} ({result['region']}): "
                  f"{result.get('products', 0):,} products in {result['duration']:.1f}s")
        else:
            print(f"❌ [{completed}/{len(functions)}] Function {result['function_id']} ({result['region']}): "
                  f"FAILED - {result.get('error', 'unknown')}")

total_duration = time.time() - start_time

# Summary
print()
print("="*70)
print("ULTRA-FAST SCRAPING COMPLETE!")
print("="*70)
print(f"⏱️  Total Time: {total_duration/60:.1f} minutes ({total_duration:.0f} seconds)")
print(f"✅ Successful Functions: {sum(1 for r in results if r['success'])}/{len(functions)}")
print(f"📦 Total Products Scraped: {total_products:,}")
print(f"📊 Total Batches Processed: {total_batches:,}")
print(f"⚡ Average Speed: {total_products/total_duration:.0f} products/second")
print(f"🎯 Success Rate: {total_products/TOTAL_PRODUCTS*100:.1f}%")
print()

# Save results
with open('ultra_scrape_results.json', 'w') as f:
    json.dump({
        'start_time': datetime.fromtimestamp(start_time).isoformat(),
        'duration_seconds': total_duration,
        'total_functions': len(functions),
        'successful_functions': sum(1 for r in results if r['success']),
        'total_products': total_products,
        'total_batches': total_batches,
        'products_per_second': total_products/total_duration,
        'success_rate': total_products/TOTAL_PRODUCTS*100,
        'results': results
    }, f, indent=2)

print("📁 Results saved to: ultra_scrape_results.json")
print()

if total_products >= TOTAL_PRODUCTS * 0.9:
    print("🎉 SUCCESS! Scraped 90%+ of all products!")
else:
    print(f"⚠️  Warning: Only scraped {total_products/TOTAL_PRODUCTS*100:.1f}% of products")
    print("   Consider re-running failed batches")
