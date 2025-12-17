# Azure Quick Start - 3 Simple Steps

## ⚡ Super Quick Guide (20 Minutes)

---

## Step 1: Gmail Setup (5 minutes) ✉️

### 1.1 Enable 2-Step Verification
```
1. Go to: https://myaccount.google.com/security
2. Click "2-Step Verification" → Enable it
```

### 1.2 Create App Password
```
1. Go to: https://myaccount.google.com/apppasswords
2. Select: Mail + Other (Custom name) → "MRO Scraper"
3. Click "Generate"


your_email@gmail.com
your_gmail_app_password
4. COPY the 16-character password (like: abcd efgh ijkl mnop)
5. Save it - you'll need it later!
```

**✅ Done! Save these:**
- Your email: `your_email@gmail.com`
- App password: `abcd efgh ijkl mnop` (16 characters)

---

## Step 2: Azure VM Setup (10 minutes) ☁️

### 2.1 Create Azure Account
```
1. Go to: https://azure.microsoft.com
2. Click "Start free"
3. Sign up (get $200 free credit!)
4. Add credit card (for verification - won't charge during trial)
```

### 2.2 Create Virtual Machine
```
1. Login to: https://portal.azure.com
2. Click "Create a resource"
3. Select "Virtual Machine"
4. Fill in:

   Resource group: Create new → "scraper-rg"
   VM name: scraper-vm
   Region: East US
   Image: Ubuntu Server 22.04 LTS
   Size: Standard_D8s_v3 (8 CPUs, 32 GB)

   Authentication: SSH public key
   Username: azureuser
   Key pair name: scraper-key

   Inbound ports: SSH (22), HTTP (80), HTTPS (443)

5. Click "Review + create"
6. Click "Create"
7. DOWNLOAD the SSH key file (.pem) - SAVE IT!
8. Wait 2 minutes for deployment
```

### 2.3 Get Your VM IP
```
1. Go to your VM in Azure Portal
2. Copy the "Public IP address" (e.g., 20.123.45.67)
3. Save it!
```

**✅ Done! Save these:**
- VM IP: `20.123.45.67` (your actual IP)
- SSH key location: `~/Downloads/scraper-key.pem`

---

## Step 3: Deploy Scraper (5 minutes) 🚀

### 3.1 Connect to VM

**Mac/Linux:**
```bash
# Move key file
mv ~/Downloads/scraper-key.pem ~/.ssh/
chmod 600 ~/.ssh/scraper-key.pem

# Connect (replace IP with yours)
ssh -i ~/.ssh/scraper-key.pem azureuser@20.123.45.67
```

**Windows PowerShell:**
```powershell
# Connect (replace IP with yours)
ssh -i C:\Users\YourName\Downloads\scraper-key.pem azureuser@20.123.45.67
```

Type "yes" when asked about fingerprint

### 3.2 Transfer Files

**On your laptop (new terminal):**

**Mac/Linux:**
```bash
cd /home/user/Desktop/mrosupply.com

rsync -avz -e "ssh -i ~/.ssh/scraper-key.pem" \
  . azureuser@20.123.45.67:/tmp/scraper/
```

**Windows PowerShell:**
```powershell
cd C:\path\to\mrosupply.com

scp -i C:\Users\YourName\Downloads\scraper-key.pem -r * azureuser@20.123.45.67:/tmp/scraper/
```

### 3.3 Install Scraper

**On VM (SSH terminal):**
```bash
cd /tmp/scraper
sudo bash deployment/setup.sh
```

Wait 5 minutes for installation...

### 3.4 Configure Credentials

```bash
sudo nano /opt/mrosupply-scraper/.env
```

**Edit these lines (replace with YOUR values):**
```bash
# Your Webshare credentials
PROXY_USER=your_webshare_username
PROXY_PASS=your_webshare_password

# Your Gmail from Step 1
SMTP_USER=your_email@gmail.com
SMTP_PASS=abcd efgh ijkl mnop  # Your 16-char app password
NOTIFICATION_EMAIL=your_email@gmail.com

# Dashboard password (choose any)
DASHBOARD_PASSWORD=MySecurePassword123

# Performance
WORKERS=50
DELAY=0.2
```

**Save:** Ctrl+X → Y → Enter

### 3.5 Test Email

```bash
sudo -u scraper /opt/mrosupply-scraper/venv/bin/python3 /opt/mrosupply-scraper/notifier.py
```

**Check your email** - should receive test message!

### 3.6 Open Dashboard Port

**In Azure Portal:**
```
1. Go to your VM
2. Click "Networking"
3. Click "Add inbound port rule"
4. Port: 8080
5. Name: Dashboard
6. Click "Add"
```

### 3.7 Start Scraper

```bash
sudo systemctl enable mrosupply-scraper
sudo systemctl start mrosupply-scraper
sudo systemctl status mrosupply-scraper
```

**✅ Should see: "Active: active (running)"**

---

## Monitor Your Scraper 📊

### View Logs
```bash
sudo journalctl -u mrosupply-scraper -f
```
Press Ctrl+C to stop viewing

### Access Dashboard

**From your laptop:**
```bash
ssh -i ~/.ssh/scraper-key.pem -L 8080:localhost:8080 azureuser@20.123.45.67
```

Keep terminal open, then open browser: **http://localhost:8080**

Login with your DASHBOARD_PASSWORD

### Check Progress

You'll receive emails:
- ✅ Startup notification (immediately)
- 📊 Progress updates (every 6 hours)
- ✅ Completion notification (after 24 hours)

---

## After Completion 🎉

### Download Results

**From your laptop:**
```bash
mkdir ~/scraper-results

scp -i ~/.ssh/scraper-key.pem \
  azureuser@20.123.45.67:/opt/mrosupply-scraper/data/*.json \
  ~/scraper-results/

scp -i ~/.ssh/scraper-key.pem \
  azureuser@20.123.45.67:/opt/mrosupply-scraper/data/*.csv \
  ~/scraper-results/
```

### Stop VM (Save Money!)

**Azure Portal:**
```
1. Go to your VM
2. Click "Stop"
3. Wait for "Stopped (deallocated)"
```

**Cost when stopped:** ~$5/month (just disk storage)

### Delete Everything (Free!)

**Azure Portal:**
```
1. Go to "Resource groups"
2. Click "scraper-rg"
3. Click "Delete resource group"
4. Type the name to confirm
5. Click "Delete"
```

**Cost after deletion:** $0

---

## Costs 💰

```
Azure VM (24 hours): $9.12
Webshare Proxy: $25.00
Total: $34.12

With $200 free credit: $9.12 (or FREE)
```

---

## Troubleshooting 🔧

### Email not working?
```bash
# Check app password in .env (no spaces!)
sudo nano /opt/mrosupply-scraper/.env

# Test again
sudo -u scraper /opt/mrosupply-scraper/venv/bin/python3 /opt/mrosupply-scraper/notifier.py
```

### Scraper not starting?
```bash
# Check logs
sudo journalctl -u mrosupply-scraper -n 50

# Restart
sudo systemctl restart mrosupply-scraper
```

### Dashboard not accessible?
```bash
# Use SSH tunnel (always works)
ssh -i ~/.ssh/scraper-key.pem -L 8080:localhost:8080 azureuser@20.123.45.67

# Then: http://localhost:8080
```

---

## That's It! 🎊

**Total Time:** 20 minutes
**Total Cost:** $34.12 (or FREE with credit)
**Products Scraped:** 1.35M+ in 24 hours
**Manual Work:** ZERO (fully autonomous)

**The scraper will:**
✅ Run for 24 hours automatically
✅ Send you progress emails
✅ Auto-restart if it crashes
✅ Handle rate limits
✅ Monitor its own health
✅ Send completion notification

**You just:**
✉️ Receive emails
📊 Check dashboard (optional)
☕ Relax!

---

## Full Guides Available

- **Complete Guide:** `AZURE_DEPLOYMENT_GUIDE.md` (detailed)
- **Usage Manual:** `USAGE.md` (all features)
- **Server Options:** `SERVER_REQUIREMENTS_24H.md` (alternatives)
- **Final Summary:** `FINAL_SUMMARY.md` (overview)

---

**Ready? Start with Step 1 (Gmail)!** 🚀
