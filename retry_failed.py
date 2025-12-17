#!/usr/bin/env python3
"""
Retry Failed URLs - Scrape only URLs that failed in previous run
"""

import sys
from pathlib import Path

# Import the main scraper
from scraper_rotating_residential import RotatingResidentialScraper

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 retry_failed.py <failed_urls_file> [output_dir]")
        print("Example: python3 retry_failed.py test_rotating_100/failed_urls_20251216_173906.txt retry_output")
        sys.exit(1)
    
    failed_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "retry_output"
    
    # Load failed URLs
    print(f"Loading failed URLs from {failed_file}...")
    with open(failed_file, 'r') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    print(f"✅ Found {len(urls)} failed URLs to retry")
    
    # Initialize scraper with optimized settings for retries
    import os
    scraper = RotatingResidentialScraper(
        proxy_host=os.getenv('PROXY_HOST', 'p.webshare.io'),
        proxy_port=int(os.getenv('PROXY_PORT', '10000')),
        proxy_user=os.getenv('PROXY_USER', 'your_username'),
        proxy_pass=os.getenv('PROXY_PASS', 'your_password'),
        output_dir=output_dir,
        workers=5,  # Fewer workers for better success rate
        delay=0.5   # Longer delay for retries
    )
    
    print("\n🔄 Retrying failed URLs with optimized settings:")
    print("   - Workers: 5 (reduced for stability)")
    print("   - Delay: 0.5s (increased for reliability)")
    print("   - Timeout: 45s (increased from 30s)")
    print("   - Retries: 3 (increased from 2)")
    
    # Scrape
    scraper.scrape_urls(urls)
    
    # Save results
    scraper.save_results()
    
    success_rate = (scraper.success_count / len(urls) * 100) if urls else 0
    print(f"\n📊 Retry Results:")
    print(f"   Success: {scraper.success_count}/{len(urls)} ({success_rate:.1f}%)")
    print(f"   Still failed: {scraper.failed_count}")
    
    if scraper.failed_count > 0:
        print(f"\n💡 Tip: Run retry again on remaining failed URLs:")
        print(f"   python3 retry_failed.py {output_dir}/failed_urls_*.txt retry_round2")
    
    print("\n✅ Retry complete!")

if __name__ == "__main__":
    main()
