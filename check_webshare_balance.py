#!/usr/bin/env python3
"""
Check Webshare API Status and Proxy Information
Shows available proxies and subscription details
"""

import requests
import sys
from datetime import datetime

# Webshare API Configuration
API_KEY = "hqy10ekhqb0jackvwe9fyzf4aosmo28wi6s48zji"
BASE_URL = "https://proxy.webshare.io/api/v2"


def get_subscription_info():
    """Get subscription information"""
    headers = {"Authorization": f"Token {API_KEY}"}

    print("=" * 70)
    print("WEBSHARE API - ACCOUNT STATUS")
    print("=" * 70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    try:
        # Get subscription details
        print("Fetching subscription information...")
        response = requests.get(f"{BASE_URL}/subscription/", headers=headers, timeout=10)

        if response.status_code != 200:
            print(f"❌ ERROR: Could not fetch subscription (Status: {response.status_code})")
            return False

        sub_data = response.json()
        print("✅ Subscription data retrieved\n")

        # Get proxy list to count available proxies
        print("Fetching proxy information...")
        response = requests.get(
            f"{BASE_URL}/proxy/list/?mode=direct&page=1&page_size=1", headers=headers, timeout=10
        )

        proxy_count = 0
        if response.status_code == 200:
            proxy_data = response.json()
            proxy_count = proxy_data.get('count', 0)
            print(f"✅ Found {proxy_count} available proxies\n")
        else:
            print("⚠️  Could not fetch proxy count\n")

        # Display subscription details
        print("=" * 70)
        print("📋 SUBSCRIPTION DETAILS")
        print("=" * 70)

        # Extract and format dates
        start_date = sub_data.get('start_date', 'Unknown')
        end_date = sub_data.get('end_date', 'Unknown')

        if start_date != 'Unknown':
            start_date = start_date.split('T')[0]
        if end_date != 'Unknown':
            end_date = end_date.split('T')[0]

        # Determine status
        throttled = sub_data.get('throttled', False)
        paused = sub_data.get('paused', False)

        status = "✅ Active"
        if paused:
            status = "⏸️  Paused"
        elif throttled:
            status = "⚠️  Throttled"

        # Plan details
        term = sub_data.get('term', 'Unknown').capitalize()
        plan_id = sub_data.get('plan', 'Unknown')

        print(f"Status:              {status}")
        print(f"Plan Type:           {term}")
        print(f"Plan ID:             {plan_id}")
        print(f"Start Date:          {start_date}")
        print(f"Renewal Date:        {end_date}")
        print(f"Available Proxies:   {proxy_count:,}")

        # Account info
        free_credits = sub_data.get('free_credits', 0)
        if free_credits > 0:
            print(f"Free Credits:        ${free_credits:.2f}")

        print()

        # Bandwidth information notice
        print("=" * 70)
        print("📊 BANDWIDTH USAGE")
        print("=" * 70)
        print("⚠️  Bandwidth usage is not available via API for this plan type.")
        print()
        print("To check your bandwidth usage (remaining of 10GB):")
        print()
        print("  1. Visit: https://proxy.webshare.io/")
        print("  2. Log in with your Webshare account")
        print("  3. Go to Dashboard → Bandwidth Usage")
        print()
        print("Your dashboard will show:")
        print("  • Total bandwidth limit (10 GB)")
        print("  • Bandwidth used")
        print("  • Bandwidth remaining")
        print("  • Usage graph over time")
        print()

        # Proxy test
        print("=" * 70)
        print("🔧 PROXY STATUS TEST")
        print("=" * 70)

        if proxy_count > 0:
            print(f"✅ {proxy_count:,} proxies are available and ready to use")
            print()
            print("Test your proxies with:")
            print("  python3 test_10k_webshare.py --webshare-api-key YOUR_KEY --workers 10 --target 100")
        else:
            print("❌ No proxies available")
            print("   Please check your subscription status on the dashboard")

        print()
        print("=" * 70)

        return True

    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: Failed to connect to Webshare API")
        print(f"   {str(e)}")
        return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False


if __name__ == "__main__":
    try:
        success = get_subscription_info()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
