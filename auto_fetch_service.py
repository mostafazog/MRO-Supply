#!/usr/bin/env python3
"""
Automated Data Fetching Service
Continuously monitors GitHub Actions and fetches new artifacts automatically
Runs as a background service and consolidates data periodically
"""

import os
import sys
import time
import json
import logging
import requests
from pathlib import Path
from datetime import datetime
import zipfile
import io
import subprocess

# Configuration
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
if not GITHUB_TOKEN:
    print("❌ Error: GITHUB_TOKEN environment variable not set")
    sys.exit(1)

REPO = os.getenv('GITHUB_REPO', 'mostafazog/MRO-Supply')
OUTPUT_DIR = Path('github_data')
CONSOLIDATED_DIR = Path('consolidated_data')
CHECK_INTERVAL = 300  # Check every 5 minutes (300 seconds)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_fetch.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutoFetchService:
    def __init__(self):
        self.headers = {
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.processed_runs = self.load_processed_runs()
        OUTPUT_DIR.mkdir(exist_ok=True)
        CONSOLIDATED_DIR.mkdir(exist_ok=True)

    def load_processed_runs(self):
        """Load set of already processed run IDs"""
        state_file = Path('processed_runs.json')
        if state_file.exists():
            with open(state_file, 'r') as f:
                return set(json.load(f))
        return set()

    def save_processed_runs(self):
        """Save processed run IDs to disk"""
        state_file = Path('processed_runs.json')
        with open(state_file, 'w') as f:
            json.dump(list(self.processed_runs), f)

    def fetch_new_artifacts(self):
        """Check for new workflow runs and fetch their artifacts"""
        try:
            # Get recent workflow runs
            runs_url = f'https://api.github.com/repos/{REPO}/actions/runs?per_page=10'
            response = requests.get(runs_url, headers=self.headers, timeout=30)
            response.raise_for_status()

            runs = response.json().get('workflow_runs', [])
            new_runs = [r for r in runs if str(r['id']) not in self.processed_runs]

            if not new_runs:
                logger.info("No new workflow runs to process")
                return 0

            logger.info(f"Found {len(new_runs)} new workflow runs to process")

            total_products = 0

            for run in new_runs:
                run_id = str(run['id'])
                run_number = run['run_number']
                status = run['status']
                conclusion = run.get('conclusion', 'N/A')

                # Only process completed runs
                if status != 'completed':
                    logger.info(f"Run #{run_number} still running, skipping for now")
                    continue

                logger.info(f"Processing Run #{run_number} - {conclusion}")

                # Get artifacts for this run
                artifacts_url = f"https://api.github.com/repos/{REPO}/actions/runs/{run['id']}/artifacts"
                artifacts_response = requests.get(artifacts_url, headers=self.headers, timeout=30)
                artifacts_response.raise_for_status()
                artifacts = artifacts_response.json().get('artifacts', [])

                if not artifacts:
                    logger.info(f"  No artifacts found for Run #{run_number}")
                    self.processed_runs.add(run_id)
                    continue

                logger.info(f"  Found {len(artifacts)} artifacts")

                for artifact in artifacts:
                    artifact_name = artifact['name']
                    artifact_size = artifact['size_in_bytes']

                    logger.info(f"  Downloading: {artifact_name} ({artifact_size:,} bytes)")

                    # Download artifact
                    download_url = artifact['archive_download_url']
                    download_response = requests.get(download_url, headers=self.headers, timeout=60)

                    if download_response.status_code == 200:
                        # Extract ZIP
                        zip_file = zipfile.ZipFile(io.BytesIO(download_response.content))

                        # Create output directory for this run
                        run_dir = OUTPUT_DIR / f"run_{run_number}"
                        run_dir.mkdir(exist_ok=True)

                        # Extract all files
                        for file_name in zip_file.namelist():
                            if file_name.endswith('.json'):
                                content = zip_file.read(file_name)
                                try:
                                    data = json.loads(content)
                                    products = data if isinstance(data, list) else data.get('products', [])
                                    product_count = len(products)
                                    total_products += product_count

                                    # Save to disk
                                    output_file = run_dir / file_name
                                    with open(output_file, 'wb') as f:
                                        f.write(content)

                                    logger.info(f"    ✓ {file_name}: {product_count} products")
                                except Exception as e:
                                    logger.error(f"    ✗ {file_name}: Invalid JSON - {e}")
                            else:
                                # Save other files
                                output_file = run_dir / file_name
                                with open(output_file, 'wb') as f:
                                    f.write(zip_file.read(file_name))
                    else:
                        logger.error(f"    ✗ Download failed: HTTP {download_response.status_code}")

                # Mark this run as processed
                self.processed_runs.add(run_id)

            # Save processed runs
            self.save_processed_runs()

            if total_products > 0:
                logger.info(f"✅ Downloaded {total_products:,} new products")
                # Trigger consolidation
                self.consolidate_data()

            return total_products

        except Exception as e:
            logger.error(f"Error fetching artifacts: {e}")
            return 0

    def consolidate_data(self):
        """Consolidate all downloaded data into single files"""
        try:
            logger.info("Consolidating data...")

            all_products = {}
            duplicate_count = 0

            # Find all JSON files
            json_files = list(OUTPUT_DIR.glob('**/*.json'))

            for json_file in json_files:
                try:
                    with open(json_file, 'r') as f:
                        data = json.load(f)

                    # Handle different data structures
                    if isinstance(data, list):
                        products = data
                    elif isinstance(data, dict):
                        products = data.get('products', data.get('results', []))
                        if not isinstance(products, list):
                            products = list(data.values()) if data else []
                    else:
                        continue

                    # Add products (deduplicate by URL)
                    for product in products:
                        if isinstance(product, dict):
                            url = product.get('url', '')
                            if url:
                                if url in all_products:
                                    duplicate_count += 1
                                else:
                                    all_products[url] = product

                except Exception as e:
                    logger.error(f"Error processing {json_file}: {e}")

            # Save consolidated JSON
            output_file = CONSOLIDATED_DIR / 'consolidated_products.json'
            with open(output_file, 'w') as f:
                json.dump(list(all_products.values()), f, indent=2)

            logger.info(f"✅ Consolidated {len(all_products):,} unique products")
            logger.info(f"   Removed {duplicate_count:,} duplicates")
            logger.info(f"   Saved to: {output_file}")

            # Also create CSV
            self.create_csv(list(all_products.values()))

        except Exception as e:
            logger.error(f"Error consolidating data: {e}")

    def create_csv(self, products):
        """Create CSV file from products"""
        try:
            import csv

            if not products:
                return

            # Get all unique field names
            fieldnames = set()
            for product in products:
                fieldnames.update(product.keys())
            fieldnames = sorted(list(fieldnames))

            # Write CSV
            csv_file = CONSOLIDATED_DIR / 'consolidated_products.csv'
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(products)

            logger.info(f"✅ CSV saved to: {csv_file}")

        except Exception as e:
            logger.error(f"Error creating CSV: {e}")

    def run(self):
        """Main service loop"""
        logger.info("=" * 60)
        logger.info("Auto-Fetch Service Started")
        logger.info(f"Repository: {REPO}")
        logger.info(f"Check interval: {CHECK_INTERVAL} seconds ({CHECK_INTERVAL//60} minutes)")
        logger.info(f"Output directory: {OUTPUT_DIR.absolute()}")
        logger.info(f"Consolidated directory: {CONSOLIDATED_DIR.absolute()}")
        logger.info("=" * 60)

        try:
            while True:
                logger.info("\n" + "="*60)
                logger.info(f"Checking for new artifacts at {datetime.now()}")

                new_products = self.fetch_new_artifacts()

                if new_products > 0:
                    logger.info(f"✅ Fetched {new_products:,} new products")
                else:
                    logger.info("No new data to fetch")

                logger.info(f"Next check in {CHECK_INTERVAL//60} minutes...")
                time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            logger.info("\n\nService stopped by user")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Service error: {e}")
            sys.exit(1)

if __name__ == '__main__':
    service = AutoFetchService()
    service.run()
