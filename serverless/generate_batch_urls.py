#!/usr/bin/env python3
"""
Generate URLs for a specific batch from the full URL list
Downloads URL file from GitHub release or generates on-the-fly
"""

import sys
import os
import argparse


def generate_urls_for_batch(batch_id: int, batch_size: int, total_urls: int = 1508714):
    """
    Generate URLs for a specific batch

    Args:
        batch_id: Batch number (0-indexed)
        batch_size: Number of URLs per batch
        total_urls: Total number of product URLs available

    Returns:
        List of URLs for this batch
    """
    # Calculate range for this batch
    start_idx = batch_id * batch_size
    end_idx = min(start_idx + batch_size, total_urls)

    # Check if URL file exists locally
    url_file = 'all_product_urls_20251215_230531.txt'

    if os.path.exists(url_file):
        print(f"Loading URLs from {url_file}...")
        with open(url_file, 'r') as f:
            all_urls = [line.strip() for line in f if line.strip()]

        batch_urls = all_urls[start_idx:end_idx]
        print(f"Loaded {len(batch_urls)} URLs for batch {batch_id}")
        return batch_urls

    # If file doesn't exist, try to download from GitHub release
    # or generate placeholder URLs
    print(f"URL file not found. Generating batch {batch_id} URLs...")

    # For now, return empty list and let the scraper handle it
    # In production, you would download the file from GitHub releases
    return []


def main():
    parser = argparse.ArgumentParser(description='Generate URLs for batch')
    parser.add_argument('--batch-id', type=int, required=True, help='Batch ID')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size')
    parser.add_argument('--total', type=int, default=1508714, help='Total URLs')
    parser.add_argument('--output', type=str, help='Output file (optional)')

    args = parser.parse_args()

    # Generate URLs
    urls = generate_urls_for_batch(args.batch_id, args.batch_size, args.total)

    # Output
    if args.output:
        with open(args.output, 'w') as f:
            f.write('\n'.join(urls))
        print(f"Saved {len(urls)} URLs to {args.output}")
    else:
        for url in urls:
            print(url)

    return 0 if urls else 1


if __name__ == '__main__':
    sys.exit(main())
