#!/usr/bin/env python3
"""
Fetch scraped data from Azure Functions
Azure Functions save data to Azure Storage (if configured)
or can query the status endpoint
"""

import os
import sys
import json
import requests
from pathlib import Path
from datetime import datetime

# Configuration
AZURE_FUNCTION_URL = os.getenv('AZURE_FUNCTION_URL', 'https://mrosupply-scraper-func.azurewebsites.net')
AZURE_FUNCTION_KEY = os.getenv('AZURE_FUNCTION_KEY', '')

def check_azure_status():
    """Check Azure Functions health and status"""
    print("Checking Azure Functions status...")
    print(f"URL: {AZURE_FUNCTION_URL}")

    # Check health endpoint
    health_url = f'{AZURE_FUNCTION_URL}/api/health'
    try:
        response = requests.get(health_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: Healthy")
            print(f"   Timestamp: {data.get('timestamp')}")
            print(f"   Function App: {data.get('function_app', 'N/A')}")
            return True
        else:
            print(f"⚠️  Status: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def fetch_azure_stats():
    """
    Fetch statistics from Azure Functions
    Note: Azure Functions save data to blob storage during GitHub Actions orchestration
    The data is collected by GitHub Actions in the 'deploy-azure' job
    """
    print("\n" + "="*60)
    print("Azure Functions Data Collection")
    print("="*60)

    print("""
Azure Functions processing is orchestrated by GitHub Actions.
The data flow is:

1. GitHub Actions triggers Azure Functions with batches
2. Azure Functions scrape and return results to GitHub Actions
3. GitHub Actions collects all results and saves to artifacts

To get Azure Functions data:
- Use fetch_github_data.py to download artifacts
- GitHub Actions artifacts contain both:
  - Data from GitHub Actions workers (50 batches)
  - Data from Azure Functions workers (remaining batches)

Current Azure Function Status:
    """)

    check_azure_status()

    print("""
Note: Azure Functions are serverless - they process on-demand
      when triggered by GitHub Actions. Data is returned to
      GitHub Actions and saved in workflow artifacts.
    """)

if __name__ == '__main__':
    try:
        fetch_azure_stats()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
