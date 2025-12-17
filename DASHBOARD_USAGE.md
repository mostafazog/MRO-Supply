# Enhanced Dashboard Usage Guide

The enhanced dashboard now monitors **all three scraping systems**:
- Local scraper
- GitHub Actions workflows
- Azure Functions

## Quick Start

### 1. Setup Environment Variables

Run the setup script:
```bash
./setup_dashboard_env.sh
```

It will prompt you for:
- GitHub Personal Access Token
- Azure Function Key
- Webshare API Key
- Proxy credentials

**Or manually create `.env` file:**
```bash
# GitHub (for workflow monitoring)
export GITHUB_TOKEN='your_github_token'
export GITHUB_REPO='mostafazog/MRO-Supply'

# Azure Functions
export AZURE_FUNCTION_URL='https://mrosupply-scraper-func.azurewebsites.net'
export AZURE_FUNCTION_KEY='your_azure_key'

# Webshare Proxy
export WEBSHARE_API_KEY='your_api_key'
export PROXY_HOST='p.webshare.io'
export PROXY_PORT='10000'
export PROXY_USER='your_username'
export PROXY_PASS='your_password'
```

### 2. Start Dashboard

```bash
# Load environment variables
source .env

# Run dashboard
python3 enhanced_dashboard.py
```

Dashboard will be available at: `http://localhost:8080`

## API Endpoints

### Local Scraper Control
- `POST /api/scraper/start` - Start local scraper
- `POST /api/scraper/stop` - Stop local scraper
- `GET /api/scraper/status` - Get scraper status

### GitHub Actions Monitoring
- `GET /api/github/workflows` - List recent workflow runs (last 5)
- `GET /api/github/workflow/<run_id>` - Get detailed workflow info with jobs

### Azure Functions Monitoring
- `GET /api/azure/status` - Check Azure Functions health
- `POST /api/azure/test` - Test scraping with sample URL

### Distributed Summary
- `GET /api/distributed/summary` - Combined status of all 3 systems

### File Management
- `GET /api/files/list` - List all output files
- `GET /api/files/download/<filename>` - Download results

### Logs
- `GET /api/logs/list` - List log files
- `GET /api/logs/view/<filename>` - View log contents
- `GET /api/logs/tail` - Get latest log entries

### System Info
- `GET /api/status` - Scraping progress
- `GET /api/system` - CPU, memory, disk usage

## Example API Calls

### Get GitHub Workflows
```bash
curl -H "Cookie: session=..." \
  http://localhost:8080/api/github/workflows
```

Response:
```json
{
  "configured": true,
  "workflows": [
    {
      "id": 20299185154,
      "name": "Distributed Scraping - GitHub Actions + Azure Functions",
      "status": "in_progress",
      "conclusion": null,
      "created_at": "2025-12-17T10:10:42Z",
      "html_url": "https://github.com/mostafazog/MRO-Supply/actions/runs/20299185154"
    }
  ]
}
```

### Get Azure Status
```bash
curl -H "Cookie: session=..." \
  http://localhost:8080/api/azure/status
```

Response:
```json
{
  "status": "healthy",
  "url": "https://mrosupply-scraper-func.azurewebsites.net",
  "timestamp": 1765965667.928739,
  "configured": true
}
```

### Get Distributed Summary
```bash
curl -H "Cookie: session=..." \
  http://localhost:8080/api/distributed/summary
```

Response:
```json
{
  "local": {
    "status": "idle"
  },
  "github": {
    "status": "in_progress",
    "name": "Distributed Scraping - GitHub Actions + Azure Functions",
    "run_id": 20299185154,
    "url": "https://github.com/mostafazog/MRO-Supply/actions/runs/20299185154"
  },
  "azure": {
    "status": "healthy",
    "url": "https://mrosupply-scraper-func.azurewebsites.net"
  }
}
```

## Features

### Real-Time Monitoring
- View all 3 systems in one dashboard
- Auto-refresh status every 30 seconds
- Click workflow links to open in GitHub

### Workflow Details
- See all jobs in a workflow
- View job status and duration
- Access logs directly

### Azure Testing
- Test Azure Functions without running full workflow
- Verify proxy configuration
- Check scraping functionality

### File Downloads
- Download scraped data (JSON/CSV)
- Access failed URLs list
- View proxy statistics

## Troubleshooting

### GitHub API Rate Limits
If you see "API rate limit exceeded":
- Wait 60 minutes, or
- Use authenticated requests (token is required)

### Azure Functions Unreachable
- Check if Azure Functions app is running in Azure Portal
- Verify AZURE_FUNCTION_URL is correct
- Test health endpoint: `curl https://mrosupply-scraper-func.azurewebsites.net/api/health`

### Missing Credentials
If endpoints return "not configured":
- Run `./setup_dashboard_env.sh` again
- Verify `.env` file exists and is loaded
- Restart dashboard after updating credentials

## Security

- Dashboard requires password authentication
- All secrets stored in `.env` (gitignored)
- Never commit credentials to Git
- Use environment variables only

## Advanced Usage

### Custom Port
```bash
# Edit config.py
DASHBOARD_PORT = 3000

# Or use environment variable
export DASHBOARD_PORT=3000
python3 enhanced_dashboard.py
```

### Remote Access
For remote monitoring via SSH tunnel:
```bash
# On server
python3 enhanced_dashboard.py

# On local machine
ssh -L 8080:localhost:8080 user@server

# Open browser
http://localhost:8080
```

### Integration with Scripts
```python
import requests

# Login
session = requests.Session()
session.post('http://localhost:8080/login', data={'password': 'your_password'})

# Get status
response = session.get('http://localhost:8080/api/distributed/summary')
data = response.json()

print(f"GitHub: {data['github']['status']}")
print(f"Azure: {data['azure']['status']}")
```

## Next Steps

1. Access dashboard: http://localhost:8080
2. Monitor GitHub Actions workflow progress
3. Check Azure Functions health
4. Download results when complete
5. View logs for debugging

For more information, see the main README.md
