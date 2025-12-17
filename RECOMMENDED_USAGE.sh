#!/bin/bash
# RECOMMENDED USAGE - MRO Supply Scraper
# This script shows the best way to run the complete system

echo "======================================================================"
echo "MRO SUPPLY SCRAPER - RECOMMENDED USAGE"
echo "======================================================================"
echo ""
echo "CURRENT STATUS:"
echo "✅ GitHub Actions: 50 workers ready"
echo "✅ Auto-fetch service: Running (downloads artifacts automatically)"
echo "✅ Dashboard: Running on port 8080"
echo "✅ Error tracking: Enabled"
echo ""
echo "======================================================================"
echo ""

echo "OPTION 1: START COMPLETE SCRAPING (RECOMMENDED)"
echo "----------------------------------------------------------------------"
echo "This will scrape all 1.5M products using GitHub Actions"
echo ""
echo "Command:"
echo "  python3 github_scraper.py"
echo ""
echo "What it does:"
echo "  - Splits 1.5M products into 15 workflows (100K each)"
echo "  - Each workflow uses 50 parallel GitHub Actions workers"
echo "  - Tracks all errors for retry"
echo "  - Waits 2 minutes between workflows"
echo "  - Saves progress after each workflow"
echo ""
echo "Time estimate: ~5-6 hours (15 workflows × 20 min each)"
echo ""
read -p "Start complete scraping? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python3 github_scraper.py
    exit 0
fi
echo ""

echo "OPTION 2: RETRY FAILED WORKFLOWS"
echo "----------------------------------------------------------------------"
echo "If some workflows failed, retry only those"
echo ""
echo "Command:"
echo "  python3 github_scraper.py --retry-failed"
echo ""
read -p "Retry failed workflows? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python3 github_scraper.py --retry-failed
    exit 0
fi
echo ""

echo "OPTION 3: MONITOR PROGRESS"
echo "----------------------------------------------------------------------"
echo ""
echo "Check scraping progress:"
echo "  cat scraping_progress.json | jq"
echo ""
echo "Check errors:"
echo "  cat scraping_errors.json | jq"
echo ""
echo "Monitor GitHub Actions:"
echo "  https://github.com/mostafazog/MRO-Supply/actions"
echo ""
echo "View consolidated data:"
echo "  ls -lh consolidated_data/"
echo ""
echo "Check auto-fetch logs:"
echo "  tail -f auto_fetch.log"
echo ""
read -p "Show current progress? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "=== PROGRESS ==="
    if [ -f scraping_progress.json ]; then
        cat scraping_progress.json | python3 -m json.tool
    else
        echo "No progress file yet"
    fi
    echo ""
    echo "=== ERRORS ==="
    if [ -f scraping_errors.json ]; then
        cat scraping_errors.json | python3 -m json.tool
    else
        echo "No errors file yet"
    fi
    echo ""
    echo "=== CONSOLIDATED DATA ==="
    ls -lh consolidated_data/ 2>/dev/null || echo "No consolidated data yet"
    exit 0
fi
echo ""

echo "OPTION 4: ACCESS DASHBOARD"
echo "----------------------------------------------------------------------"
echo ""
echo "Dashboard URL: http://172.173.144.149:8080"
echo "Password: admin123"
echo ""
echo "Dashboard features:"
echo "  - Real-time workflow monitoring"
echo "  - GitHub Actions status"
echo "  - System metrics"
echo "  - Log viewer"
echo "  - File browser"
echo "  - Trigger workflows"
echo ""
read -p "Open dashboard instructions? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "To access dashboard:"
    echo "  1. Open browser"
    echo "  2. Go to: http://172.173.144.149:8080"
    echo "  3. Enter password: admin123"
    echo "  4. Click 'Monitor' tab to see real-time status"
    echo ""
fi
echo ""

echo "======================================================================"
echo "QUICK REFERENCE"
echo "======================================================================"
echo ""
echo "Start scraping:      python3 github_scraper.py"
echo "Retry failures:      python3 github_scraper.py --retry-failed"
echo "Check progress:      cat scraping_progress.json | jq"
echo "Check errors:        cat scraping_errors.json | jq"
echo "View data:           ls -lh consolidated_data/"
echo "Auto-fetch logs:     tail -f auto_fetch.log"
echo "Dashboard:           http://172.173.144.149:8080"
echo "GitHub Actions:      https://github.com/mostafazog/MRO-Supply/actions"
echo ""
echo "======================================================================"
echo ""
