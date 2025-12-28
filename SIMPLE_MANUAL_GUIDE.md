# Simple Manual 100K Scraping Guide

## Easiest Way - Use Distributed Scraper Directly

Instead of the wrapper workflow, just use the main distributed scraper with specific batch ranges.

###  How to Run Each 100K Batch

1. Go to: https://github.com/mostafazog/MRO-Supply/actions/workflows/distributed-scrape-image-filter.yml
2. Click "Run workflow"
3. Enter these values:
   - **github_workers**: `18`
   - **start_batch**: (see table below)
   - **end_batch**: (see table below)
4. Click "Run workflow"
5. Wait 2-3 hours
6. Download results from artifacts

---

## Batch Ranges for Each Run

| Run | start_batch | end_batch | Products      | Command |
|-----|-------------|-----------|---------------|---------|
| 1   | 0           | 1000      | 0-100K        | `gh workflow run distributed-scrape-image-filter.yml --field github_workers=18 --field start_batch=0 --field end_batch=1000` |
| 2   | 1000        | 2000      | 100K-200K     | `gh workflow run distributed-scrape-image-filter.yml --field github_workers=18 --field start_batch=1000 --field end_batch=2000` |
| 3   | 2000        | 3000      | 200K-300K     | `gh workflow run distributed-scrape-image-filter.yml --field github_workers=18 --field start_batch=2000 --field end_batch=3000` |
| 4   | 3000        | 4000      | 300K-400K     | `gh workflow run distributed-scrape-image-filter.yml --field github_workers=18 --field start_batch=3000 --field end_batch=4000` |
| 5   | 4000        | 5000      | 400K-500K     | `gh workflow run distributed-scrape-image-filter.yml --field github_workers=18 --field start_batch=4000 --field end_batch=5000` |
| 6   | 5000        | 6000      | 500K-600K     | `gh workflow run distributed-scrape-image-filter.yml --field github_workers=18 --field start_batch=5000 --field end_batch=6000` |
| 7   | 6000        | 7000      | 600K-700K     | `gh workflow run distributed-scrape-image-filter.yml --field github_workers=18 --field start_batch=6000 --field end_batch=7000` |
| 8   | 7000        | 8000      | 700K-800K     | `gh workflow run distributed-scrape-image-filter.yml --field github_workers=18 --field start_batch=7000 --field end_batch=8000` |
| 9   | 8000        | 9000      | 800K-900K     | `gh workflow run distributed-scrape-image-filter.yml --field github_workers=18 --field start_batch=8000 --field end_batch=9000` |
| 10  | 9000        | 10000     | 900K-1M       | `gh workflow run distributed-scrape-image-filter.yml --field github_workers=18 --field start_batch=9000 --field end_batch=10000` |
| 11  | 10000       | 11000     | 1M-1.1M       | `gh workflow run distributed-scrape-image-filter.yml --field github_workers=18 --field start_batch=10000 --field end_batch=11000` |
| 12  | 11000       | 12000     | 1.1M-1.2M     | `gh workflow run distributed-scrape-image-filter.yml --field github_workers=18 --field start_batch=11000 --field end_batch=12000` |
| 13  | 12000       | 13000     | 1.2M-1.3M     | `gh workflow run distributed-scrape-image-filter.yml --field github_workers=18 --field start_batch=12000 --field end_batch=13000` |
| 14  | 13000       | 14000     | 1.3M-1.4M     | `gh workflow run distributed-scrape-image-filter.yml --field github_workers=18 --field start_batch=13000 --field end_batch=14000` |
| 15  | 14000       | 15088     | 1.4M-1.5M     | `gh workflow run distributed-scrape-image-filter.yml --field github_workers=18 --field start_batch=14000 --field end_batch=15088` |

---

## Progress Tracking

- [ ] Run 1: 0-100K
- [ ] Run 2: 100K-200K  
- [ ] Run 3: 200K-300K
- [ ] Run 4: 300K-400K
- [ ] Run 5: 400K-500K
- [ ] Run 6: 500K-600K
- [ ] Run 7: 600K-700K
- [ ] Run 8: 700K-800K
- [ ] Run 9: 800K-900K
- [ ] Run 10: 900K-1M
- [ ] Run 11: 1M-1.1M
- [ ] Run 12: 1.1M-1.2M
- [ ] Run 13: 1.2M-1.3M
- [ ] Run 14: 1.3M-1.4M
- [ ] Run 15: 1.4M-1.5M

---

## After Each Run

1. Go to: https://github.com/mostafazog/MRO-Supply/actions
2. Click on the completed run
3. Scroll down to "Artifacts"
4. Download "final-results"
5. Extract and import to PrestaShop
6. Check off the run above
7. Wait 6-12 hours before next run (to avoid rate limiting)
8. Start next run

---

## Example: Running Batch 1

**Via GitHub Web UI:**
1. Go to https://github.com/mostafazog/MRO-Supply/actions/workflows/distributed-scrape-image-filter.yml
2. Click "Run workflow" 
3. Set:
   - github_workers: 18
   - start_batch: 0
   - end_batch: 1000
4. Click green "Run workflow" button

**Via Command Line:**
```bash
gh workflow run distributed-scrape-image-filter.yml \
  --field github_workers=18 \
  --field start_batch=0 \
  --field end_batch=1000
```

---

## Tips

- **Timing**: Run during off-peak hours (midnight-6am)
- **Spacing**: Wait 6-12 hours between runs
- **Monitoring**: Each run should complete in 2-3 hours
- **Rate Limiting**: If you see lots of 429 errors, wait longer between runs

---

## This Approach Works!

This is the same workflow that successfully scraped your previous 47K products.
We're just running it in smaller chunks to stay under GitHub's 6-hour timeout.
