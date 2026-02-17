# 🚀 HOW TO UPLOAD BRAND LOGOS TO YOUR SERVER

## ✅ What's Ready

All **36 brand logos** are now in your GitHub repository:
- ✅ 10 REAL logos from MRO Supply (Alemite, Bando, FKB Bearings, etc.)
- ✅ 26 Professional text placeholders
- ✅ All pushed to GitHub at commit `627a552`

## 📦 Files Uploaded to GitHub

```
CORRECT_BRAND_LOGOS/
├── 1.jpg (Bando - Real logo)
├── 222.jpg (Alemite - Real logo)
├── 223.jpg (WWE - Real logo)
├── ... (33 more logos)
└── 249.jpg (Yarinind Tools - Text placeholder)

upload_brand_logos.php (Upload script)
.github/workflows/upload-brand-logos.yml (Automated workflow)
```

## 🎯 METHOD 1: GitHub Actions (Automated) - RECOMMENDED

### Step 1: Go to GitHub Actions
1. Visit: https://github.com/mostafazog/MRO-Supply/actions
2. Click on **"Upload Brand Logos to PrestaShop"** workflow (left sidebar)
3. Click **"Run workflow"** button (right side)
4. Select branch: **main**
5. Click green **"Run workflow"** button

### Step 2: Wait for Completion
- Workflow will take 1-2 minutes
- It will automatically:
  - ✅ Upload all 36 logos to `/img/m/` directory
  - ✅ Run the PHP upload script
  - ✅ Clear PrestaShop cache
  - ✅ Set correct file permissions

### Step 3: Verify Upload
Visit: https://www.yarinind.com/brands

You should see all brands with their logos!

---

## 🖥️ METHOD 2: Manual Upload via SSH

If you have SSH access:

```bash
# Clone the repository (if not already)
git clone https://github.com/mostafazog/MRO-Supply.git
cd MRO-Supply

# Pull latest changes
git pull origin main

# Upload logos via SCP
scp CORRECT_BRAND_LOGOS/*.jpg hstgr-srv1164617@srv1164617.hstgr.cloud:/home/hstgr-srv1164617/htdocs/srv1164617.hstgr.cloud/img/m/

# SSH into server and run upload script
ssh hstgr-srv1164617@srv1164617.hstgr.cloud
cd /home/hstgr-srv1164617/htdocs/srv1164617.hstgr.cloud
php upload_brand_logos.php

# Clear cache
rm -rf var/cache/prod/* var/cache/dev/*
rm -rf cache/smarty/compile/* cache/smarty/cache/*
```

---

## 📂 METHOD 3: Manual Upload via FileZilla/cPanel

### Option A: FileZilla/SFTP

1. **Download logos from GitHub:**
   - Go to: https://github.com/mostafazog/MRO-Supply/tree/main/CORRECT_BRAND_LOGOS
   - Click "Code" → "Download ZIP"
   - Extract `CORRECT_BRAND_LOGOS/` folder

2. **Connect to server:**
   - Host: `srv1164617.hstgr.cloud`
   - Protocol: SFTP
   - Username: `hstgr-srv1164617`
   - Port: 22

3. **Upload logos:**
   - Navigate to: `/home/hstgr-srv1164617/htdocs/srv1164617.hstgr.cloud/img/m/`
   - Upload all `.jpg` files from `CORRECT_BRAND_LOGOS/` folder

4. **Clear cache via cPanel or SSH:**
   ```bash
   cd /home/hstgr-srv1164617/htdocs/srv1164617.hstgr.cloud
   rm -rf var/cache/prod/* var/cache/dev/*
   ```

### Option B: cPanel File Manager

1. **Login to cPanel**
2. **Open File Manager**
3. **Navigate to:**
   `/home/hstgr-srv1164617/htdocs/srv1164617.hstgr.cloud/img/m/`
4. **Upload all 36 .jpg files** from CORRECT_BRAND_LOGOS folder
5. **Open Terminal in cPanel** and run:
   ```bash
   cd /home/hstgr-srv1164617/htdocs/srv1164617.hstgr.cloud
   rm -rf var/cache/prod/* var/cache/dev/* cache/smarty/compile/* cache/smarty/cache/*
   ```

---

## 🔍 Verify Upload Success

After upload, check:

### ✅ Brands Page
Visit: https://www.yarinind.com/brands

You should see:
- ✅ Alemite with RED logo (droplet shape)
- ✅ Bando with real brand logo
- ✅ Mitutoyo with real brand logo
- ✅ Text-based logos for brands without real logos
- ❌ NO MORE wrong Wikipedia images (bison, people photos, etc.)

### ✅ Admin Panel
Visit: https://www.yarinind.com/admin → Catalog → Brands

Each brand should show its logo in the list.

---

## 🐛 Troubleshooting

### Problem: Logos don't appear after upload

**Solution 1: Clear browser cache**
- Press `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)

**Solution 2: Clear PrestaShop cache**
```bash
ssh hstgr-srv1164617@srv1164617.hstgr.cloud
cd /home/hstgr-srv1164617/htdocs/srv1164617.hstgr.cloud
rm -rf var/cache/prod/* var/cache/dev/*
rm -rf cache/smarty/compile/* cache/smarty/cache/*
```

**Solution 3: Check file permissions**
```bash
chmod 644 /home/hstgr-srv1164617/htdocs/srv1164617.hstgr.cloud/img/m/*.jpg
```

---

## 📊 What Was Fixed

### BEFORE ❌
- Wrong images from Wikipedia (bison animal, Halle Bailey photo, Star Wars blaster)
- Only 1-2 real logos
- Most were text placeholders or incorrect images

### AFTER ✅
- 10 REAL brand logos from MRO Supply S3 bucket
- 26 Professional text-based placeholders
- NO wrong Wikipedia images
- All logos properly formatted (JPG, white background)

---

## 📋 Logo Summary

### Real Logos (10):
1. **Alemite** - Red droplet logo
2. **Bando** - Official brand logo
3. **Bestt Liebco** - Real logo
4. **FKB Bearings** - Real logo
5. **Grove Gear** - Real logo
6. **Hub City** - Real logo
7. **Mitutoyo** - Real logo
8. **US Tsubaki** - Real logo
9. **WWE** - Real logo
10. **Zero Max** - Real logo

### Text Placeholders (26):
All other brands (Goulds, LSIS, HPS Transformers, Eaton, Carlisle Belts, RMT, Sigma, CPS Products, Stieber Clutch, Hanson Tools, Nidec Motors, Palmgren, Omega Engineering, Flowdrill, Wrapflex, GPI, Generac, Nebo Tools, UAB, Mako, West Chester, Kopflex, Remco, Modicon, Superior Electric, Yarinind Tools)

---

## ✅ Quick Start (Recommended)

**Easiest method: Use GitHub Actions**

1. Go to: https://github.com/mostafazog/MRO-Supply/actions
2. Click "Upload Brand Logos to PrestaShop"
3. Click "Run workflow" → Select "main" → Click "Run workflow"
4. Wait 1-2 minutes
5. Visit: https://www.yarinind.com/brands

Done! All logos uploaded automatically. 🎉

---

## 📞 Need Help?

If the GitHub Actions workflow fails, check the workflow logs at:
https://github.com/mostafazog/MRO-Supply/actions

Or use Manual Upload Method 2 or 3 above.
