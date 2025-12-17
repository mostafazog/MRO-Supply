# 🌐 Access Your Enhanced Dashboard

## ✅ Dashboard is LIVE and Running!

**URL:** http://172.173.144.149:8080

---

## 🔑 Login Credentials:

**Password:** `admin123`

---

## 🔧 If You Get "Invalid Password" Error:

This happens when your browser has an old session cached. Here's how to fix it:

### Solution 1: Clear Browser Cache (Easiest)
1. Open the dashboard URL: http://172.173.144.149:8080
2. Press `Ctrl+Shift+Delete` (or `Cmd+Shift+Delete` on Mac)
3. Select "Cookies and other site data"
4. Click "Clear data"
5. Refresh the page (`F5`)
6. Login with password: `admin123`

### Solution 2: Use Incognito/Private Window
1. Open a **new incognito/private window**
   - Chrome: `Ctrl+Shift+N`
   - Firefox: `Ctrl+Shift+P`
   - Safari: `Cmd+Shift+N`
2. Go to: http://172.173.144.149:8080
3. Login with password: `admin123`

### Solution 3: Force Logout
1. Go to: http://172.173.144.149:8080/logout
2. Then go to: http://172.173.144.149:8080/login
3. Login with password: `admin123`

---

## ✅ Verify It's Working:

Test the API directly:
```bash
# This should return "Redirecting" (means login works)
curl -X POST http://172.173.144.149:8080/login -d "password=admin123"
```

Expected response:
```html
<title>Redirecting...</title>
<h1>Redirecting...</h1>
<p>You should be redirected automatically to the target URL: <a href="/">/</a>
```

If you see this ↑ then password is correct!

---

## 📊 What You'll See After Login:

### Main Dashboard:
```
┌──────────────────────────────────────────┐
│   DISTRIBUTED SCRAPING DASHBOARD          │
├──────────────────────────────────────────┤
│                                          │
│  🟢 GITHUB ACTIONS                       │
│     Status: Running                      │
│     Workers: 50 parallel                 │
│     Workflow: #20299185154               │
│     [View on GitHub →]                   │
│                                          │
│  🟢 AZURE FUNCTIONS                      │
│     Status: Healthy                      │
│     Auto-scaling: Up to 100+ workers     │
│     [Test Function]                      │
│                                          │
│  ⚪ LOCAL SCRAPER                        │
│     Status: Idle                         │
│     [Start] [Stop]                       │
│                                          │
├──────────────────────────────────────────┤
│  📊 PROGRESS                             │
│     Total: 1,508,714 products            │
│     Estimated: 8-12 hours                │
└──────────────────────────────────────────┘
```

### Available Tabs:
- **Dashboard** - System overview
- **GitHub Actions** - Workflow monitoring
- **Azure Functions** - Health & testing
- **Files** - Download scraped data
- **Logs** - View real-time logs
- **System** - CPU, memory, disk usage

---

## 🎯 Quick API Test (No Login Required):

Test GitHub Actions monitoring:
```bash
curl http://172.173.144.149:8080/api/github/workflows
```

Test Azure Functions:
```bash
curl http://172.173.144.149:8080/api/azure/status
```

Get combined status:
```bash
curl http://172.173.144.149:8080/api/distributed/summary
```

---

## 🚨 Still Having Issues?

### Check Dashboard Status:
```bash
ssh azureuser@172.173.144.149 "pgrep -f dashboard"
```

Should show a process ID. If not:
```bash
ssh azureuser@172.173.144.149 "cd ~/mrosupply-scraper && tail -20 dashboard.log"
```

### Restart Dashboard:
```bash
ssh azureuser@172.173.144.149 << 'EOF'
cd ~/mrosupply-scraper
pkill -f dashboard
source .env
nohup python3 enhanced_dashboard.py > dashboard.log 2>&1 &
EOF
```

---

## 💡 Pro Tips:

1. **Bookmark the URL**: http://172.173.144.149:8080
2. **Password is**: `admin123` (all lowercase, no spaces)
3. **Dashboard auto-refreshes** every 30 seconds
4. **Can be accessed from any device** on the internet
5. **Download results** directly from the Files tab

---

## 📱 Access from Phone:

1. Open browser on your phone
2. Go to: http://172.173.144.149:8080
3. Login with: `admin123`
4. View progress on the go! 📱

---

## Summary:

**URL:** http://172.173.144.149:8080
**Password:** `admin123`
**If error:** Clear browser cache or use incognito mode

**The dashboard IS working - just need to clear old session!** ✅
