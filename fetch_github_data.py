#!/usr/bin/env python3
"""
Fetch scraped data from GitHub Actions artifacts
Downloads all artifacts from recent workflow runs
"""

import os
import sys
import json
import requests
from pathlib import Path
from datetime import datetime
import zipfile
import io

# Configuration
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
if not GITHUB_TOKEN:
    print("❌ Error: GITHUB_TOKEN environment variable not set")
    print("   Usage: export GITHUB_TOKEN='your_token_here'")
    print("   Then run: python3 fetch_github_data.py")
    sys.exit(1)

REPO = 'mostafazog/MRO-Supply'
OUTPUT_DIR = Path('github_data')

def fetch_artifacts():
    """Fetch all artifacts from recent workflow runs"""
    OUTPUT_DIR.mkdir(exist_ok=True)

    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }

    # Get recent workflow runs
    print("Fetching workflow runs...")
    runs_url = f'https://api.github.com/repos/{REPO}/actions/runs?per_page=10'
    response = requests.get(runs_url, headers=headers)
    runs = response.json().get('workflow_runs', [])

    print(f"Found {len(runs)} recent workflow runs")

    total_products = 0

    for run in runs:
        run_number = run['run_number']
        status = run['status']
        conclusion = run.get('conclusion', 'N/A')

        print(f"\n{'='*60}")
        print(f"Run #{run_number} - Status: {status} - Conclusion: {conclusion}")
        print(f"URL: {run['html_url']}")

        # Get artifacts for this run
        artifacts_url = f"https://api.github.com/repos/{REPO}/actions/runs/{run['id']}/artifacts"
        artifacts_response = requests.get(artifacts_url, headers=headers)
        artifacts = artifacts_response.json().get('artifacts', [])

        print(f"Found {len(artifacts)} artifacts")

        for artifact in artifacts:
            artifact_name = artifact['name']
            artifact_size = artifact['size_in_bytes']

            print(f"\n  Downloading: {artifact_name} ({artifact_size:,} bytes)")

            # Download artifact
            download_url = artifact['archive_download_url']
            download_response = requests.get(download_url, headers=headers)

            if download_response.status_code == 200:
                # Extract ZIP
                zip_file = zipfile.ZipFile(io.BytesIO(download_response.content))

                # Create output directory for this run
                run_dir = OUTPUT_DIR / f"run_{run_number}"
                run_dir.mkdir(exist_ok=True)

                # Extract all files
                for file_name in zip_file.namelist():
                    if file_name.endswith('.json'):
                        # Extract and count products
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

                            print(f"    ✓ {file_name}: {product_count} products")
                        except:
                            print(f"    ✗ {file_name}: Invalid JSON")
                    else:
                        # Save other files
                        output_file = run_dir / file_name
                        with open(output_file, 'wb') as f:
                            f.write(zip_file.read(file_name))
            else:
                print(f"    ✗ Download failed: HTTP {download_response.status_code}")

    print(f"\n{'='*60}")
    print(f"✅ Total products downloaded: {total_products:,}")
    print(f"📁 Data saved to: {OUTPUT_DIR.absolute()}")

if __name__ == '__main__':
    try:
        fetch_artifacts()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
