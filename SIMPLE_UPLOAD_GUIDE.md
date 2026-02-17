# 🚀 SIMPLEST WAY TO UPLOAD LOGOS - 3 COMMANDS!

## ✅ All 36 Brand Logos Are Ready

- ✅ 10 REAL logos from MRO Supply (Alemite, Bando, Mitutoyo, etc.)
- ✅ 26 Professional text placeholders
- ✅ All pushed to GitHub and ready to download

---

## 🎯 UPLOAD METHOD: Run These 3 Commands on Your Server

### Option 1: Via cPanel Terminal

1. **Login to your cPanel**
2. **Open Terminal** (Advanced → Terminal)
3. **Copy and paste these commands** one by one:

```bash
cd /home/hstgr-srv1164617/htdocs/srv1164617.hstgr.cloud

wget https://raw.githubusercontent.com/mostafazog/MRO-Supply/main/upload_via_php.php -O upload_logos.php

php upload_logos.php

rm upload_logos.php
```

**Done!** All 36 logos will be uploaded automatically.

---

### Option 2: Via SSH

If you have SSH access:

```bash
ssh hstgr-srv1164617@srv1164617.hstgr.cloud

cd /home/hstgr-srv1164617/htdocs/srv1164617.hstgr.cloud

wget https://raw.githubusercontent.com/mostafazog/MRO-Supply/main/upload_via_php.php -O upload_logos.php

php upload_logos.php

rm upload_logos.php
```

---

## 📊 What These Commands Do

1. **`cd /home/.../srv1164617.hstgr.cloud`** - Navigate to your PrestaShop directory
2. **`wget ...`** - Download the uploader script from GitHub
3. **`php upload_logos.php`** - Run the script to:
   - Download all 36 logos from GitHub
   - Install them to `/img/m/` directory
   - Set correct permissions (644)
   - Clear PrestaShop cache
   - Show detailed progress report
4. **`rm upload_logos.php`** - Delete the uploader (security cleanup)

---

## ✨ What You'll See

The PHP script will show:
```
✓ Found 36 logo files to download
✓ [  1] 1.jpg → Installed (13.2 KB)
✓ [222] 222.jpg → Installed (50.8 KB)
✓ [243] 243.jpg → Installed (68.4 KB)
...
✅ UPLOAD COMPLETE!
  ✓ Uploaded: 36 logos
  ✓ 10 REAL logos from MRO Supply
  ✓ 26 Text placeholders
```

---

## 🔍 Verify Upload

After running the commands, visit:

### 1. Brands Page
https://www.yarinind.com/brands

You should see:
- ✅ **Alemite** - Professional red droplet logo
- ✅ **Bando** - Real brand logo
- ✅ **Mitutoyo** - Real brand logo
- ✅ **Hub City** - Real brand logo
- ✅ **US Tsubaki** - Real brand logo
- ✅ **Zero Max** - Real brand logo
- ✅ And 30 more brands with correct images

### 2. Admin Panel
https://www.yarinind.com/admin → Catalog → Brands

All 36 brands should display their logos.

---

## 🐛 Troubleshooting

### Problem: "wget: command not found"
Use `curl` instead:
```bash
curl https://raw.githubusercontent.com/mostafazog/MRO-Supply/main/upload_via_php.php -o upload_logos.php
```

### Problem: "Permission denied"
Make sure you're in the correct directory:
```bash
ls -la /home/hstgr-srv1164617/htdocs/srv1164617.hstgr.cloud/img/m/
```

If permission issues, run:
```bash
chmod 755 /home/hstgr-srv1164617/htdocs/srv1164617.hstgr.cloud/img/m/
```

### Problem: Logos don't appear
Clear browser cache:
- `Ctrl+Shift+R` (Windows/Linux)
- `Cmd+Shift+R` (Mac)

---

## 📋 Before and After

### BEFORE ❌
- Wrong images from Wikipedia:
  - BISON → Bison animal
  - Baileigh → Halle Bailey photo
  - BLASTER → Star Wars blaster
  - Carlisle Belts → Belinda Carlisle (singer)
  - DAYTON → City skyline photo

### AFTER ✅
- 10 REAL brand logos from MRO Supply
- 26 Professional text placeholders
- NO wrong Wikipedia images
- All images properly formatted

---

## ⏱️ Time Required

- **2 minutes** to login to cPanel
- **30 seconds** to run the 4 commands
- **1 minute** for upload to complete
- **Total: 3-4 minutes**

---

## 🎉 THAT'S IT!

Just run those 3 commands on your server and all logos will be uploaded automatically.

No SSH keys, no passwords, no complicated setup - just 3 simple commands!

---

## 📞 Support

If you encounter any issues:
1. Check `/home/hstgr-srv1164617/htdocs/srv1164617.hstgr.cloud/img/m/` has write permissions
2. Make sure PHP is installed (`php -v`)
3. Verify internet connectivity (`ping google.com`)

All 36 logo files are available on GitHub:
https://github.com/mostafazog/MRO-Supply/tree/main/CORRECT_BRAND_LOGOS
