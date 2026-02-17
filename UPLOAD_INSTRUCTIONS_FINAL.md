# 🚀 UPLOAD BRAND LOGOS - EASIEST METHODS

## ✅ What's Ready

All **36 brand logos** are prepared and waiting to be uploaded:
- ✅ 10 REAL logos from MRO Supply (Alemite, Bando, Mitutoyo, etc.)
- ✅ 26 Professional text placeholders
- ✅ All images properly formatted (JPG, white background)
- ✅ Files ready in: `CORRECT_BRAND_LOGOS/` folder

---

## 🎯 METHOD 1: PHP Remote Uploader (EASIEST - NO PASSWORD NEEDED)

This method downloads logos directly from GitHub to your server. **No SSH or password required!**

### Step 1: Upload the PHP Script

Upload `upload_via_php.php` to your server root directory using:
- **cPanel File Manager**, or
- **FileZilla/FTP**, or
- **Any file manager your hosting provides**

Target location: `/home/hstgr-srv1164617/htdocs/srv1164617.hstgr.cloud/upload_via_php.php`

### Step 2: Run the Script

Simply visit this URL in your browser:

```
https://www.yarinind.com/upload_via_php.php
```

The script will:
1. ✅ Download all 36 logos from GitHub
2. ✅ Install them to `/img/m/` directory
3. ✅ Set correct file permissions (644)
4. ✅ Clear PrestaShop cache
5. ✅ Show you a detailed progress report

### Step 3: Delete the Script (Security)

After successful upload, delete the file:
```bash
rm /home/hstgr-srv1164617/htdocs/srv1164617.hstgr.cloud/upload_via_php.php
```

Or delete it via cPanel File Manager.

### Step 4: Verify

Visit: https://www.yarinind.com/brands

You should see all brands with their logos!

---

## 🖥️ METHOD 2: Direct Upload via cPanel File Manager

If you prefer manual upload:

### Step 1: Download Logos

The logos are in: `/media/sda2/coding projet/mrosupply.com/CORRECT_BRAND_LOGOS/`

Or download from GitHub:
https://github.com/mostafazog/MRO-Supply/tree/main/CORRECT_BRAND_LOGOS

### Step 2: Upload via cPanel

1. **Login to cPanel**
2. **Open File Manager**
3. **Navigate to:** `/home/hstgr-srv1164617/htdocs/srv1164617.hstgr.cloud/img/m/`
4. **Upload all 36 .jpg files** from `CORRECT_BRAND_LOGOS/` folder
5. **Select all uploaded files** → Right-click → **Change Permissions** → Set to **644**

### Step 3: Clear Cache

In cPanel, open **Terminal** and run:

```bash
cd /home/hstgr-srv1164617/htdocs/srv1164617.hstgr.cloud
rm -rf var/cache/prod/* var/cache/dev/*
rm -rf cache/smarty/compile/* cache/smarty/cache/*
```

Or use the **Clear Cache** button in PrestaShop admin panel.

### Step 4: Verify

Visit: https://www.yarinind.com/brands

---

## 📊 METHOD 3: GitHub Actions (If SSH credentials are configured)

If you have SSH credentials set up in GitHub Secrets:

1. Visit: https://github.com/mostafazog/MRO-Supply/actions
2. Click: **"Upload Brand Logos to PrestaShop"** workflow
3. Click: **"Run workflow"** button
4. Select branch: **main**
5. Click: **"Run workflow"**

This will automatically upload all logos via SSH.

---

## ✨ What You'll See After Upload

### On https://www.yarinind.com/brands:

**Real Logos (10 brands):**
- ✅ **Alemite** - Professional red droplet logo
- ✅ **Bando** - Official brand logo
- ✅ **Bestt Liebco** - Real logo
- ✅ **FKB Bearings** - Real logo
- ✅ **Grove Gear** - Real logo
- ✅ **Hub City** - Real logo
- ✅ **Mitutoyo** - Real logo
- ✅ **US Tsubaki** - Real logo
- ✅ **WWE (World Wide Electric)** - Real logo
- ✅ **Zero Max** - Real logo

**Text Placeholders (26 brands):**
- Clean, professional text-based logos for all other brands

**NO MORE:**
- ❌ Bison animal image for "BISON" brand
- ❌ Halle Bailey photo for "Baileigh" brand
- ❌ Star Wars blaster for "BLASTER" brand
- ❌ Wrong Wikipedia images

### On Admin Panel:

Visit: https://www.yarinind.com/admin → Catalog → Brands

All 36 brands should show their logos in the brand list.

---

## 🐛 Troubleshooting

### Problem: Logos don't appear after upload

**Solution 1: Clear Browser Cache**
- Press `Ctrl+Shift+R` (Windows/Linux)
- Press `Cmd+Shift+R` (Mac)

**Solution 2: Clear PrestaShop Cache**
```bash
cd /home/hstgr-srv1164617/htdocs/srv1164617.hstgr.cloud
rm -rf var/cache/prod/* var/cache/dev/*
rm -rf cache/smarty/compile/* cache/smarty/cache/*
```

**Solution 3: Check File Permissions**
```bash
chmod 644 /home/hstgr-srv1164617/htdocs/srv1164617.hstgr.cloud/img/m/*.jpg
```

**Solution 4: Check File Existence**
```bash
ls -la /home/hstgr-srv1164617/htdocs/srv1164617.hstgr.cloud/img/m/ | grep -E "(1|222|243)\.jpg"
```

### Problem: Permission denied when uploading

**Solution:**
```bash
chmod 755 /home/hstgr-srv1164617/htdocs/srv1164617.hstgr.cloud/img/m
```

---

## 📋 Complete Logo List

### Real Logos from MRO Supply (10):
| ID | Brand | Status |
|----|-------|--------|
| 1 | Bando | ✅ Real logo |
| 221 | FKB Bearings | ✅ Real logo |
| 222 | Alemite | ✅ Real logo |
| 223 | WWE (World Wide Electric) | ✅ Real logo |
| 227 | Hub City | ✅ Real logo |
| 228 | US Tsubaki | ✅ Real logo |
| 237 | Grove Gear | ✅ Real logo |
| 239 | Zero Max | ✅ Real logo |
| 243 | Mitutoyo | ✅ Real logo |
| 244 | Bestt Liebco | ✅ Real logo |

### Text Placeholders (26):
| ID | Brand | Status |
|----|-------|--------|
| 2 | Goulds | 📝 Text placeholder |
| 216 | LSIS | 📝 Text placeholder |
| 217 | HPS Transformers | 📝 Text placeholder |
| 218 | Eaton | 📝 Text placeholder |
| 219 | Carlisle Belts | 📝 Text placeholder |
| 220 | RMT | 📝 Text placeholder |
| 224 | Sigma | 📝 Text placeholder |
| 225 | CPS Products | 📝 Text placeholder |
| 226 | Stieber Clutch | 📝 Text placeholder |
| 229 | Hanson Tools | 📝 Text placeholder |
| 230 | Nidec Motors | 📝 Text placeholder |
| 231 | Palmgren | 📝 Text placeholder |
| 232 | Omega Engineering | 📝 Text placeholder |
| 233 | Flowdrill | 📝 Text placeholder |
| 234 | Wrapflex | 📝 Text placeholder |
| 235 | GPI | 📝 Text placeholder |
| 236 | Generac | 📝 Text placeholder |
| 238 | Nebo Tools | 📝 Text placeholder |
| 240 | UAB | 📝 Text placeholder |
| 241 | Mako | 📝 Text placeholder |
| 242 | West Chester | 📝 Text placeholder |
| 245 | Kopflex | 📝 Text placeholder |
| 246 | Remco | 📝 Text placeholder |
| 247 | Modicon | 📝 Text placeholder |
| 248 | Superior Electric | 📝 Text placeholder |
| 249 | Yarinind Tools | 📝 Text placeholder |

---

## 🎉 RECOMMENDED: Use Method 1 (PHP Remote Uploader)

**Why Method 1 is best:**
- ✅ No SSH or password needed
- ✅ No command line required
- ✅ Works through web browser
- ✅ Automatic progress tracking
- ✅ Automatic cache clearing
- ✅ One-click solution

**Just 3 steps:**
1. Upload `upload_via_php.php` to your server (via cPanel)
2. Visit `https://www.yarinind.com/upload_via_php.php` in browser
3. Delete the PHP file after completion

**Done!** All 36 logos will be installed automatically.

---

## 📞 Files Location

**Local PC:**
- `/media/sda2/coding projet/mrosupply.com/CORRECT_BRAND_LOGOS/`
- `/media/sda2/coding projet/mrosupply.com/upload_via_php.php`

**GitHub:**
- https://github.com/mostafazog/MRO-Supply/tree/main/CORRECT_BRAND_LOGOS
- https://github.com/mostafazog/MRO-Supply/blob/main/upload_via_php.php

**Server Target:**
- `/home/hstgr-srv1164617/htdocs/srv1164617.hstgr.cloud/img/m/`

---

## ✅ Summary

**Status:** ✅ READY FOR UPLOAD

**Recommended Method:** PHP Remote Uploader (Method 1)

**Time Required:** 2-3 minutes

**Difficulty:** Easy (web browser only)

**Result:** All 36 brand logos installed with correct images!
