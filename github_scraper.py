#!/usr/bin/env python3
"""
GitHub Actions Intelligent Scraper
Uses only GitHub Actions with error tracking and retry
"""

import json
import requests
import time
import os
from datetime import datetime
from pathlib import Path

# Configuration
TOTAL_PRODUCTS = 1_508_714
BATCH_SIZE = 100
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')  # Set via environment variable
REPO = "mostafazog/MRO-Supply"

if not GITHUB_TOKEN:
    print("ERROR: GITHUB_TOKEN environment variable not set!")
    print("Set it with: export GITHUB_TOKEN='your_token_here'")
    exit(1)

# File paths
ERROR_LOG = Path("scraping_errors.json")
PROGRESS_LOG = Path("scraping_progress.json")
RESULTS_LOG = Path("scraping_results.json")

print("="*70)
print("GITHUB ACTIONS INTELLIGENT SCRAPER")
print("50 Workers with Error Tracking & Retry")
print("="*70)
print()

class GitHubScraper:
    def __init__(self):
        self.total_batches = (TOTAL_PRODUCTS + BATCH_SIZE - 1) // BATCH_SIZE
        self.errors = self.load_errors()
        self.progress = self.load_progress()
        self.headers = {
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json'
        }

    def load_errors(self):
        """Load previous errors for retry"""
        if ERROR_LOG.exists():
            with open(ERROR_LOG, 'r') as f:
                data = json.load(f)
                failed = data.get('failed_workflows', [])
                print(f"📋 Loaded {len(failed)} failed workflows from previous run")
                return data
        return {'failed_workflows': []}

    def save_errors(self):
        """Save errors for later retry"""
        with open(ERROR_LOG, 'w') as f:
            json.dump(self.errors, f, indent=2)
        print(f"💾 Saved {len(self.errors['failed_workflows'])} failed workflows to {ERROR_LOG}")

    def load_progress(self):
        """Load scraping progress"""
        if PROGRESS_LOG.exists():
            with open(PROGRESS_LOG, 'r') as f:
                data = json.load(f)
                print(f"📊 Loaded progress: {data.get('total_products_scraped', 0):,} products scraped")
                return data
        return {
            'completed_workflows': [],
            'total_products_scraped': 0,
            'last_run': None
        }

    def save_progress(self):
        """Save scraping progress"""
        self.progress['last_run'] = datetime.now().isoformat()
        with open(PROGRESS_LOG, 'w') as f:
            json.dump(self.progress, f, indent=2)

    def trigger_workflow(self, workflow_num, products_per_workflow):
        """Trigger GitHub Actions workflow"""
        payload = {
            'ref': 'main',  # Using main branch
            'inputs': {
                'total_products': str(products_per_workflow),
                'batch_size': str(BATCH_SIZE),
                'use_azure_functions': 'false',  # Don't use Azure
                'github_workers': '50'  # 50 parallel workers
            }
        }

        try:
            response = requests.post(
                f'https://api.github.com/repos/{REPO}/actions/workflows/distributed-scrape-azure.yml/dispatches',
                headers=self.headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 204:
                print(f"   ✅ Workflow #{workflow_num} triggered: {products_per_workflow:,} products")
                return {
                    'success': True,
                    'workflow_num': workflow_num,
                    'products': products_per_workflow,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                error_msg = f'HTTP {response.status_code}'
                print(f"   ❌ Workflow #{workflow_num} failed: {error_msg}")
                return {
                    'success': False,
                    'workflow_num': workflow_num,
                    'products': products_per_workflow,
                    'error': error_msg,
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            error_msg = str(e)
            print(f"   ❌ Workflow #{workflow_num} failed: {error_msg}")
            return {
                'success': False,
                'workflow_num': workflow_num,
                'products': products_per_workflow,
                'error': error_msg,
                'timestamp': datetime.now().isoformat()
            }

    def run_scrape(self):
        """
        Intelligent scraping strategy:
        1. Split 1.5M products into chunks of 50K each (smaller to avoid timeout)
        2. Trigger GitHub Actions workflows sequentially
        3. Track errors for retry
        4. Wait between workflows to avoid rate limits
        """

        print("📊 Scraping Strategy:")
        print(f"   Total products: {TOTAL_PRODUCTS:,}")
        print(f"   Total batches: {self.total_batches:,}")
        print(f"   Products per workflow: 50,000")
        print(f"   GitHub Actions workers: 50 per workflow")
        print()

        # Calculate chunks (50K products = 500 batches per workflow)
        products_per_workflow = 50_000  # Reduced from 100K to avoid GitHub timeout
        batches_per_workflow = products_per_workflow // BATCH_SIZE
        num_workflows = (TOTAL_PRODUCTS + products_per_workflow - 1) // products_per_workflow

        print(f"🚀 LAUNCHING WORKFLOWS")
        print(f"   Will trigger {num_workflows} workflows")
        print(f"   Each workflow: {products_per_workflow:,} products")
        print(f"   Wait time between workflows: 2 minutes")
        print()

        # Ensure errors dict has correct structure
        if 'failed_workflows' not in self.errors:
            self.errors['failed_workflows'] = []

        results = []
        for i in range(num_workflows):
            start_product = i * products_per_workflow
            products_in_chunk = min(products_per_workflow, TOTAL_PRODUCTS - start_product)

            print(f"🎯 Workflow {i+1}/{num_workflows}")
            print(f"   Products: {start_product:,} to {start_product + products_in_chunk:,}")

            result = self.trigger_workflow(i+1, products_in_chunk)
            results.append(result)

            if result['success']:
                self.progress['completed_workflows'].append(i+1)
                self.progress['total_products_scraped'] += products_in_chunk
            else:
                self.errors['failed_workflows'].append(result)

            # Save progress after each workflow
            self.save_progress()
            self.save_errors()

            # Wait between workflows to avoid rate limits
            if i < num_workflows - 1:
                print(f"   ⏳ Waiting 2 minutes before next workflow...")
                print()
                time.sleep(120)

        # Final summary
        print()
        print("="*70)
        print("SCRAPING COMPLETE")
        print("="*70)
        success_count = sum(1 for r in results if r['success'])
        print(f"✅ Successful workflows: {success_count}/{num_workflows}")
        print(f"❌ Failed workflows: {len(self.errors['failed_workflows'])}")
        print(f"📦 Products queued: ~{self.progress['total_products_scraped']:,}")
        print()
        print(f"💾 Progress saved to: {PROGRESS_LOG}")
        print(f"💾 Errors saved to: {ERROR_LOG}")
        print()

        if self.errors['failed_workflows']:
            print("⚠️  Some workflows failed. To retry:")
            print("   python3 github_scraper.py --retry-failed")
        else:
            print("🎉 All workflows triggered successfully!")

        print()
        print("📊 Monitor workflows at:")
        print(f"   https://github.com/{REPO}/actions")
        print()

        # Save final results
        results_data = {
            'timestamp': datetime.now().isoformat(),
            'total_workflows': num_workflows,
            'completed_workflows': len(self.progress['completed_workflows']),
            'failed_workflows': len(self.errors['failed_workflows']),
            'estimated_products': self.progress['total_products_scraped']
        }

        with open(RESULTS_LOG, 'w') as f:
            json.dump(results_data, f, indent=2)

        print(f"📊 Results saved to: {RESULTS_LOG}")
        print()

    def retry_failed_workflows(self):
        """Retry only failed workflows"""
        if not self.errors['failed_workflows']:
            print("✅ No failed workflows to retry!")
            return

        print(f"🔄 Retrying {len(self.errors['failed_workflows'])} failed workflows...")
        print()

        failed = self.errors['failed_workflows'].copy()
        self.errors['failed_workflows'] = []  # Clear for new attempts

        for i, workflow in enumerate(failed):
            workflow_num = workflow['workflow_num']
            products = workflow['products']

            print(f"🎯 Retry {i+1}/{len(failed)}: Workflow #{workflow_num}")
            result = self.trigger_workflow(workflow_num, products)

            if result['success']:
                self.progress['completed_workflows'].append(workflow_num)
                self.progress['total_products_scraped'] += products
            else:
                self.errors['failed_workflows'].append(result)

            self.save_progress()
            self.save_errors()

            if i < len(failed) - 1:
                print(f"   ⏳ Waiting 2 minutes...")
                print()
                time.sleep(120)

        print()
        print("="*70)
        print("RETRY COMPLETE")
        print("="*70)
        print(f"✅ Successful: {len(failed) - len(self.errors['failed_workflows'])}/{len(failed)}")
        print(f"❌ Still failing: {len(self.errors['failed_workflows'])}")
        print()

if __name__ == '__main__':
    import sys

    scraper = GitHubScraper()

    if '--retry-failed' in sys.argv:
        scraper.retry_failed_workflows()
    else:
        scraper.run_scrape()
