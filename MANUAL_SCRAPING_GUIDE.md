# Manual 100K Product Scraping Guide

## Overview
This guide helps you scrape all 1.5M products from MRO Supply in manageable 100K chunks.

**Why 100K chunks?**
- ✅ Each run takes 2-3 hours (well under GitHub's 6-hour limit)
- ✅ Easier to manage and monitor
- ✅ Can import to PrestaShop after each successful run
- ✅ Less risk - if one fails, you only lose 100K, not everything

## Total Progress

**Total Products:** 1,508,714
**Runs Needed:** 15
**Products per Run:** ~100,000
**Time per Run:** 2-3 hours
**Total Estimated Time:** 30-45 hours of scraping (spread over days/weeks)

---

## How to Run Each Batch

### Via GitHub Actions UI (Easiest)

1. Go to: https://github.com/mostafazog/MRO-Supply/actions/workflows/manual-100k-scrape.yml
2. Click **"Run workflow"** button
3. Select the **run number** from dropdown (1-15)
4. Click **"Run workflow"** green button
5. Monitor at: https://github.com/mostafazog/MRO-Supply/actions

### Via Command Line

```bash
gh workflow run manual-100k-scrape.yml --field run_number=1
```

---

## Run Schedule

Track your progress by checking off completed runs:

### Batch 1: Products 0 - 100K
- [ ] **Run 1** - Batches 0-1000
- Command: `gh workflow run manual-100k-scrape.yml --field run_number=1`
- Status: ⏳ Pending

### Batch 2: Products 100K - 200K
- [ ] **Run 2** - Batches 1000-2000
- Command: `gh workflow run manual-100k-scrape.yml --field run_number=2`
- Status: ⏳ Pending

### Batch 3: Products 200K - 300K
- [ ] **Run 3** - Batches 2000-3000
- Command: `gh workflow run manual-100k-scrape.yml --field run_number=3`
- Status: ⏳ Pending

### Batch 4: Products 300K - 400K
- [ ] **Run 4** - Batches 3000-4000
- Command: `gh workflow run manual-100k-scrape.yml --field run_number=4`
- Status: ⏳ Pending

### Batch 5: Products 400K - 500K
- [ ] **Run 5** - Batches 4000-5000
- Command: `gh workflow run manual-100k-scrape.yml --field run_number=5`
- Status: ⏳ Pending

### Batch 6: Products 500K - 600K
- [ ] **Run 6** - Batches 5000-6000
- Command: `gh workflow run manual-100k-scrape.yml --field run_number=6`
- Status: ⏳ Pending

### Batch 7: Products 600K - 700K
- [ ] **Run 7** - Batches 6000-7000
- Command: `gh workflow run manual-100k-scrape.yml --field run_number=7`
- Status: ⏳ Pending

### Batch 8: Products 700K - 800K
- [ ] **Run 8** - Batches 7000-8000
- Command: `gh workflow run manual-100k-scrape.yml --field run_number=8`
- Status: ⏳ Pending

### Batch 9: Products 800K - 900K
- [ ] **Run 9** - Batches 8000-9000
- Command: `gh workflow run manual-100k-scrape.yml --field run_number=9`
- Status: ⏳ Pending

### Batch 10: Products 900K - 1M
- [ ] **Run 10** - Batches 9000-10000
- Command: `gh workflow run manual-100k-scrape.yml --field run_number=10`
- Status: ⏳ Pending

### Batch 11: Products 1M - 1.1M
- [ ] **Run 11** - Batches 10000-11000
- Command: `gh workflow run manual-100k-scrape.yml --field run_number=11`
- Status: ⏳ Pending

### Batch 12: Products 1.1M - 1.2M
- [ ] **Run 12** - Batches 11000-12000
- Command: `gh workflow run manual-100k-scrape.yml --field run_number=12`
- Status: ⏳ Pending

### Batch 13: Products 1.2M - 1.3M
- [ ] **Run 13** - Batches 12000-13000
- Command: `gh workflow run manual-100k-scrape.yml --field run_number=13`
- Status: ⏳ Pending

### Batch 14: Products 1.3M - 1.4M
- [ ] **Run 14** - Batches 13000-14000
- Command: `gh workflow run manual-100k-scrape.yml --field run_number=14`
- Status: ⏳ Pending

### Batch 15: Products 1.4M - 1.5M
- [ ] **Run 15** - Batches 14000-15088
- Command: `gh workflow run manual-100k-scrape.yml --field run_number=15`
- Status: ⏳ Pending

---

## After Each Successful Run

1. **Download the results**
   ```bash
   gh run download <RUN_ID> --dir results/run_<NUMBER>
   ```

2. **Verify the data**
   - Check that products have images
   - Check for proper titles, prices, descriptions

3. **Import to PrestaShop**
   - Use your existing import process
   - Import the JSON/CSV file to PrestaShop

4. **Mark as complete** (check the box above)

5. **Start next run** when ready

---

## Tips for Success

### Timing
- ⏰ Run during off-peak hours (midnight-6am) for better success rates
- 😴 Space runs out by 6-12 hours to avoid rate limiting
- 📅 Can run 2-3 per day safely

### Monitoring
- 👀 Check GitHub Actions page regularly
- ⏱️ Each run should complete in 2-3 hours
- 🚨 If a run takes longer than 4 hours, something might be wrong

### If a Run Fails
- ❌ Don't panic! Only 100K products affected
- 🔄 Wait 12 hours and retry the same run number
- 📊 Check the logs to see how far it got
- 💾 You might have partial data you can still use

### Rate Limiting
- If you get lots of 429 errors, wait longer between runs
- Consider running only 1-2 batches per day
- The server needs rest periods between heavy scraping

---

## Custom Batch Ranges

If you need to scrape a custom range:

```bash
gh workflow run manual-100k-scrape.yml \
  --field run_number=custom \
  --field custom_start_batch=500 \
  --field custom_end_batch=1500
```

---

## Troubleshooting

### Run Failed After 6 Hours
- **Cause:** GitHub's hard 6-hour timeout
- **Solution:** This shouldn't happen with 100K chunks, but if it does, reduce workers or chunk size

### Too Many Rate Limit Errors
- **Cause:** Server is blocking your requests
- **Solution:** Wait 24 hours before next run, reduce workers to 12

### No Artifacts Uploaded
- **Cause:** Run was cancelled or failed before completion
- **Solution:** Retry the same run number

---

## Progress Tracking

Keep notes here:

```
Date       | Run # | Status  | Products Scraped | Imported to PrestaShop
-----------|-------|---------|------------------|----------------------
           |       |         |                  |
           |       |         |                  |
           |       |         |                  |
```

---

## Questions?

Check the workflow logs at:
https://github.com/mostafazog/MRO-Supply/actions
