#!/bin/bash
# Test Raptor Supplies GitHub Actions worker locally

echo "=========================================="
echo "Testing Raptor Supplies Worker Locally"
echo "=========================================="
echo ""

# Set environment variables
export WORKER_ID=0
export TOTAL_WORKERS=1
export TOTAL_PRODUCTS=5
export START_INDEX=0
export USE_BROWSER=false  # Set to true to test browser mode

echo "Configuration:"
echo "  Worker ID: $WORKER_ID"
echo "  Total Workers: $TOTAL_WORKERS"
echo "  Total Products: $TOTAL_PRODUCTS (will scrape 5 products)"
echo "  Browser Mode: $USE_BROWSER"
echo ""

# Check if URLs file exists
if [ ! -f "raptorsupplies_urls.json" ]; then
    echo "❌ raptorsupplies_urls.json not found!"
    echo "This file should contain 89,155 product URLs"
    exit 1
fi

echo "✅ Found raptorsupplies_urls.json"
echo ""

# Run worker
echo "🚀 Starting worker..."
echo ""

python3 raptorsupplies_github_worker.py

# Check results
echo ""
echo "=========================================="
echo "Checking Results"
echo "=========================================="

if [ -f "worker_0_products.json" ]; then
    COUNT=$(cat worker_0_products.json | python3 -c "import sys, json; print(len(json.load(sys.stdin)))")
    echo "✅ Products scraped: $COUNT"
    echo ""
    echo "Sample product:"
    cat worker_0_products.json | python3 -m json.tool | head -30
else
    echo "❌ No products file generated"
fi

if [ -f "worker_0_errors.json" ]; then
    ERROR_COUNT=$(cat worker_0_errors.json | python3 -c "import sys, json; print(len(json.load(sys.stdin)))")
    echo ""
    echo "⚠️  Errors: $ERROR_COUNT"
fi

echo ""
echo "=========================================="
echo "Test Complete"
echo "=========================================="
