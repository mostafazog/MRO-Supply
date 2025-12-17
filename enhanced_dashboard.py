#!/usr/bin/env python3
"""
Enhanced Web Dashboard for MRO Supply Scraper
Flask-based monitoring and control interface with full management capabilities
Includes GitHub Actions and Azure Functions monitoring
"""

import os
import json
import time
import subprocess
import signal
import logging
import requests
from pathlib import Path
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from werkzeug.security import check_password_hash, generate_password_hash

logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))

# Configuration
DASHBOARD_PASSWORD = None
OUTPUT_DIR = None
CONFIG = None
SCRAPER_PROCESS = None
SCRAPER_PID_FILE = Path('scraper.pid')


def init_dashboard(config):
    """Initialize dashboard with configuration"""
    global DASHBOARD_PASSWORD, OUTPUT_DIR, CONFIG

    CONFIG = config
    OUTPUT_DIR = Path(config.OUTPUT_DIR)

    # Hash the password for security
    DASHBOARD_PASSWORD = generate_password_hash(
        config.DASHBOARD_PASSWORD,
        method='pbkdf2:sha256'
    )

    logger.info(f"Dashboard initialized on port {config.DASHBOARD_PORT}")


def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        password = request.form.get('password')

        if DASHBOARD_PASSWORD and check_password_hash(DASHBOARD_PASSWORD, password):
            session['logged_in'] = True
            session['login_time'] = time.time()
            logger.info("Dashboard login successful")
            return redirect(url_for('index'))
        else:
            logger.warning("Dashboard login failed")
            return render_template('login.html', error="Invalid password")

    return render_template('login.html')


@app.route('/logout')
def logout():
    """Logout"""
    session.pop('logged_in', None)
    session.pop('login_time', None)
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    """Main dashboard page"""
    return render_template('enhanced_dashboard.html')


# ========== SCRAPER CONTROL ENDPOINTS ==========

@app.route('/api/scraper/start', methods=['POST'])
@login_required
def start_scraper():
    """Start the scraper"""
    try:
        data = request.json or {}

        # Check if already running
        if is_scraper_running():
            return jsonify({
                'success': False,
                'message': 'Scraper is already running',
                'pid': get_scraper_pid()
            }), 400

        # Get parameters
        script = data.get('script', 'production_scraper_webshare.py')
        max_products = data.get('max_products', None)
        workers = data.get('workers', 10)

        # Build command
        cmd = ['python3', script]

        if max_products:
            cmd.extend(['--max-products', str(max_products)])
        if workers:
            cmd.extend(['--workers', str(workers)])

        # Start scraper in background
        log_file = OUTPUT_DIR / 'scraper_latest.log'
        with open(log_file, 'w') as f:
            process = subprocess.Popen(
                cmd,
                stdout=f,
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid
            )

        # Save PID
        with open(SCRAPER_PID_FILE, 'w') as f:
            f.write(str(process.pid))

        logger.info(f"Scraper started with PID {process.pid}")

        return jsonify({
            'success': True,
            'message': 'Scraper started successfully',
            'pid': process.pid,
            'script': script,
            'log_file': str(log_file)
        })

    except Exception as e:
        logger.error(f"Error starting scraper: {e}")
        return jsonify({
            'success': False,
            'message': f'Error starting scraper: {str(e)}'
        }), 500


@app.route('/api/scraper/stop', methods=['POST'])
@login_required
def stop_scraper():
    """Stop the scraper"""
    try:
        pid = get_scraper_pid()

        if not pid:
            return jsonify({
                'success': False,
                'message': 'No scraper process found'
            }), 404

        # Send SIGTERM for graceful shutdown
        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
            logger.info(f"Sent SIGTERM to scraper PID {pid}")

            # Wait a bit for graceful shutdown
            time.sleep(2)

            # Check if still running
            if is_process_running(pid):
                # Force kill
                os.killpg(os.getpgid(pid), signal.SIGKILL)
                logger.warning(f"Force killed scraper PID {pid}")

            # Clean up PID file
            if SCRAPER_PID_FILE.exists():
                SCRAPER_PID_FILE.unlink()

            return jsonify({
                'success': True,
                'message': 'Scraper stopped successfully',
                'pid': pid
            })

        except ProcessLookupError:
            # Process already dead
            if SCRAPER_PID_FILE.exists():
                SCRAPER_PID_FILE.unlink()
            return jsonify({
                'success': True,
                'message': 'Scraper was not running'
            })

    except Exception as e:
        logger.error(f"Error stopping scraper: {e}")
        return jsonify({
            'success': False,
            'message': f'Error stopping scraper: {str(e)}'
        }), 500


@app.route('/api/scraper/status')
@login_required
def scraper_status():
    """Get scraper process status"""
    try:
        pid = get_scraper_pid()
        running = is_scraper_running()

        status_info = {
            'running': running,
            'pid': pid if running else None
        }

        if running and pid:
            # Get process info
            try:
                result = subprocess.run(
                    ['ps', '-p', str(pid), '-o', 'etime,cmd'],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) > 1:
                        parts = lines[1].strip().split(None, 1)
                        status_info['uptime'] = parts[0] if parts else 'Unknown'
                        status_info['command'] = parts[1] if len(parts) > 1 else 'Unknown'
            except Exception as e:
                logger.error(f"Error getting process info: {e}")

        return jsonify(status_info)

    except Exception as e:
        logger.error(f"Error getting scraper status: {e}")
        return jsonify({'error': str(e)}), 500


# ========== LOG VIEWING ==========

@app.route('/api/logs/list')
@login_required
def list_logs():
    """List available log files"""
    try:
        log_files = []

        # Find all log files
        for log_file in sorted(OUTPUT_DIR.glob('*.log'), key=lambda x: x.stat().st_mtime, reverse=True):
            log_files.append({
                'name': log_file.name,
                'size': log_file.stat().st_size,
                'modified': datetime.fromtimestamp(log_file.stat().st_mtime).isoformat()
            })

        return jsonify({'logs': log_files})

    except Exception as e:
        logger.error(f"Error listing logs: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/logs/view/<filename>')
@login_required
def view_log(filename):
    """View log file contents"""
    try:
        log_file = OUTPUT_DIR / filename

        if not log_file.exists() or not log_file.name.endswith('.log'):
            return jsonify({'error': 'Log file not found'}), 404

        # Get tail lines (default 100)
        lines = int(request.args.get('lines', 100))

        # Read last N lines
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
            tail_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines

        return jsonify({
            'filename': filename,
            'lines': ''.join(tail_lines),
            'total_lines': len(all_lines)
        })

    except Exception as e:
        logger.error(f"Error viewing log: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/logs/tail')
@login_required
def tail_log():
    """Get real-time log tail (latest log file)"""
    try:
        # Find latest log file
        log_files = sorted(OUTPUT_DIR.glob('scraper_log_*.log'), key=lambda x: x.stat().st_mtime)

        if not log_files:
            # Try latest log
            latest_log = OUTPUT_DIR / 'scraper_latest.log'
            if not latest_log.exists():
                return jsonify({'lines': '', 'message': 'No log files found'})
            log_file = latest_log
        else:
            log_file = log_files[-1]

        lines = int(request.args.get('lines', 50))

        with open(log_file, 'r') as f:
            all_lines = f.readlines()
            tail_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines

        return jsonify({
            'filename': log_file.name,
            'lines': ''.join(tail_lines),
            'total_lines': len(all_lines)
        })

    except Exception as e:
        logger.error(f"Error tailing log: {e}")
        return jsonify({'error': str(e)}), 500


# ========== FILE DOWNLOADS ==========

@app.route('/api/files/list')
@login_required
def list_files():
    """List downloadable files"""
    try:
        files = []

        # Patterns to match
        patterns = [
            'products_*.json',
            'products_*.csv',
            'failed_urls_*.txt',
            'proxy_stats_*.json',
            'checkpoint_products.json'
        ]

        for pattern in patterns:
            for file_path in OUTPUT_DIR.glob(pattern):
                files.append({
                    'name': file_path.name,
                    'size': file_path.stat().st_size,
                    'size_mb': round(file_path.stat().st_size / (1024 * 1024), 2),
                    'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                    'type': file_path.suffix[1:]  # Extension without dot
                })

        # Sort by modified time (newest first)
        files.sort(key=lambda x: x['modified'], reverse=True)

        return jsonify({'files': files})

    except Exception as e:
        logger.error(f"Error listing files: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/files/download/<filename>')
@login_required
def download_file(filename):
    """Download a file"""
    try:
        file_path = OUTPUT_DIR / filename

        if not file_path.exists():
            return jsonify({'error': 'File not found'}), 404

        # Security check - ensure file is in OUTPUT_DIR
        if not file_path.resolve().is_relative_to(OUTPUT_DIR.resolve()):
            return jsonify({'error': 'Access denied'}), 403

        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        return jsonify({'error': str(e)}), 500


# ========== CONFIGURATION MANAGEMENT ==========

@app.route('/api/config/webshare', methods=['GET', 'POST'])
@login_required
def manage_webshare():
    """Get or update Webshare API key"""
    try:
        env_file = Path('.env')

        if request.method == 'GET':
            # Read current API key
            api_key = os.getenv('WEBSHARE_API_KEY', '')

            # Mask the key for display (show last 4 chars)
            if api_key and len(api_key) > 4:
                masked_key = '*' * (len(api_key) - 4) + api_key[-4:]
            else:
                masked_key = '****'

            return jsonify({
                'api_key': masked_key,
                'configured': bool(api_key)
            })

        elif request.method == 'POST':
            # Update API key
            data = request.json
            new_api_key = data.get('api_key', '').strip()

            if not new_api_key:
                return jsonify({
                    'success': False,
                    'message': 'API key cannot be empty'
                }), 400

            # Read .env file
            if env_file.exists():
                with open(env_file, 'r') as f:
                    lines = f.readlines()
            else:
                lines = []

            # Update or add WEBSHARE_API_KEY
            found = False
            for i, line in enumerate(lines):
                if line.startswith('WEBSHARE_API_KEY='):
                    lines[i] = f'WEBSHARE_API_KEY={new_api_key}\n'
                    found = True
                    break

            if not found:
                lines.append(f'WEBSHARE_API_KEY={new_api_key}\n')

            # Write back
            with open(env_file, 'w') as f:
                f.writelines(lines)

            # Update environment variable
            os.environ['WEBSHARE_API_KEY'] = new_api_key

            logger.info("Webshare API key updated")

            return jsonify({
                'success': True,
                'message': 'API key updated successfully. Restart scraper for changes to take effect.'
            })

    except Exception as e:
        logger.error(f"Error managing Webshare key: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


# ========== ORIGINAL MONITORING ENDPOINTS ==========

@app.route('/api/status')
@login_required
def api_status():
    """Get current scraping status"""
    try:
        checkpoint_file = OUTPUT_DIR / 'checkpoint_products.json'

        if not checkpoint_file.exists():
            return jsonify({
                'status': 'idle',
                'message': 'No scraping in progress',
                'completed': 0,
                'total': 0,
                'percent': 0
            })

        with open(checkpoint_file, 'r') as f:
            checkpoint = json.load(f)

        completed = len(checkpoint)
        total = getattr(CONFIG, 'TOTAL_URLS', 1500000) if CONFIG else 1500000
        percent = (completed / total * 100) if total > 0 else 0
        file_age = time.time() - checkpoint_file.stat().st_mtime
        is_stale = file_age > 600

        return jsonify({
            'status': 'stale' if is_stale else 'running',
            'completed': completed,
            'total': total,
            'percent': round(percent, 2),
            'last_update': datetime.fromtimestamp(checkpoint_file.stat().st_mtime).isoformat(),
            'file_age_seconds': round(file_age, 0)
        })

    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/system')
@login_required
def api_system():
    """Get system resources"""
    try:
        import psutil

        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage(str(OUTPUT_DIR))

        return jsonify({
            'cpu_percent': round(cpu_percent, 1),
            'memory_percent': round(memory.percent, 1),
            'memory_used_gb': round(memory.used / (1024 ** 3), 2),
            'memory_total_gb': round(memory.total / (1024 ** 3), 2),
            'disk_free_gb': round(disk.free / (1024 ** 3), 2),
            'disk_total_gb': round(disk.total / (1024 ** 3), 2),
            'disk_percent': round(disk.percent, 1),
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return jsonify({'error': str(e)}), 500


# ========== GITHUB ACTIONS MONITORING ==========

@app.route('/api/github/workflows')
@login_required
def github_workflows():
    """Get GitHub Actions workflow status"""
    try:
        github_token = os.getenv('GITHUB_TOKEN', '')
        repo = os.getenv('GITHUB_REPO', 'mostafazog/MRO-Supply')

        if not github_token:
            return jsonify({
                'error': 'GITHUB_TOKEN not configured',
                'configured': False
            })

        # Get latest workflow runs
        url = f'https://api.github.com/repos/{repo}/actions/runs'
        headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }

        response = requests.get(url, headers=headers, params={'per_page': 5}, timeout=10)

        if response.status_code != 200:
            return jsonify({
                'error': f'GitHub API returned {response.status_code}',
                'configured': True
            }), response.status_code

        data = response.json()

        # Parse workflow runs
        workflows = []
        for run in data.get('workflow_runs', []):
            workflows.append({
                'id': run['id'],
                'name': run['name'],
                'status': run['status'],
                'conclusion': run.get('conclusion'),
                'created_at': run['created_at'],
                'updated_at': run['updated_at'],
                'html_url': run['html_url'],
                'run_number': run['run_number']
            })

        return jsonify({
            'configured': True,
            'workflows': workflows,
            'total_count': data.get('total_count', 0)
        })

    except Exception as e:
        logger.error(f"Error getting GitHub workflows: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/github/workflow/<int:run_id>')
@login_required
def github_workflow_details(run_id):
    """Get detailed information about a specific workflow run"""
    try:
        github_token = os.getenv('GITHUB_TOKEN', '')
        repo = os.getenv('GITHUB_REPO', 'mostafazog/MRO-Supply')

        if not github_token:
            return jsonify({'error': 'GITHUB_TOKEN not configured'}), 500

        headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }

        # Get workflow run details
        url = f'https://api.github.com/repos/{repo}/actions/runs/{run_id}'
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            return jsonify({'error': f'GitHub API returned {response.status_code}'}), response.status_code

        run_data = response.json()

        # Get jobs for this run
        jobs_url = f'https://api.github.com/repos/{repo}/actions/runs/{run_id}/jobs'
        jobs_response = requests.get(jobs_url, headers=headers, timeout=10)

        jobs = []
        if jobs_response.status_code == 200:
            for job in jobs_response.json().get('jobs', []):
                jobs.append({
                    'id': job['id'],
                    'name': job['name'],
                    'status': job['status'],
                    'conclusion': job.get('conclusion'),
                    'started_at': job.get('started_at'),
                    'completed_at': job.get('completed_at'),
                    'html_url': job['html_url']
                })

        return jsonify({
            'run': {
                'id': run_data['id'],
                'name': run_data['name'],
                'status': run_data['status'],
                'conclusion': run_data.get('conclusion'),
                'created_at': run_data['created_at'],
                'updated_at': run_data['updated_at'],
                'html_url': run_data['html_url'],
                'run_number': run_data['run_number']
            },
            'jobs': jobs,
            'jobs_count': len(jobs)
        })

    except Exception as e:
        logger.error(f"Error getting workflow details: {e}")
        return jsonify({'error': str(e)}), 500


# ========== AZURE FUNCTIONS MONITORING ==========

@app.route('/api/azure/status')
@login_required
def azure_status():
    """Get Azure Functions status"""
    try:
        azure_url = os.getenv('AZURE_FUNCTION_URL', 'https://mrosupply-scraper-func.azurewebsites.net')

        # Check health endpoint
        health_url = f'{azure_url}/api/health'

        try:
            response = requests.get(health_url, timeout=10)

            if response.status_code == 200:
                health_data = response.json()
                return jsonify({
                    'status': 'healthy',
                    'url': azure_url,
                    'timestamp': health_data.get('timestamp'),
                    'configured': True
                })
            else:
                return jsonify({
                    'status': 'unhealthy',
                    'url': azure_url,
                    'error': f'HTTP {response.status_code}',
                    'configured': True
                })

        except requests.exceptions.RequestException as e:
            return jsonify({
                'status': 'unreachable',
                'url': azure_url,
                'error': str(e),
                'configured': True
            })

    except Exception as e:
        logger.error(f"Error checking Azure status: {e}")
        return jsonify({'error': str(e), 'configured': False}), 500


@app.route('/api/azure/test', methods=['POST'])
@login_required
def azure_test_scrape():
    """Test Azure Functions scraping endpoint"""
    try:
        azure_url = os.getenv('AZURE_FUNCTION_URL', 'https://mrosupply-scraper-func.azurewebsites.net')
        azure_key = os.getenv('AZURE_FUNCTION_KEY', '')

        # Test URL
        test_urls = ['https://www.mrosupply.com/automation/2302938_ant-gw715153_red-lion-controls/']

        scrape_url = f'{azure_url}/api/scrape'
        params = {'code': azure_key} if azure_key else {}

        response = requests.post(
            scrape_url,
            params=params,
            json={'urls': test_urls, 'batch_id': 999},
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            return jsonify({
                'success': True,
                'batch_id': result.get('batch_id'),
                'total': result.get('total'),
                'success_count': result.get('success'),
                'failed_count': result.get('failed'),
                'test_url': test_urls[0]
            })
        else:
            return jsonify({
                'success': False,
                'error': f'HTTP {response.status_code}',
                'message': response.text[:200]
            }), response.status_code

    except Exception as e:
        logger.error(f"Error testing Azure function: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/distributed/summary')
@login_required
def distributed_summary():
    """Get combined summary of all distributed scraping systems"""
    try:
        summary = {
            'local': {'status': 'unknown'},
            'github': {'status': 'unknown'},
            'azure': {'status': 'unknown'}
        }

        # Local scraper status
        if is_scraper_running():
            summary['local'] = {
                'status': 'running',
                'pid': get_scraper_pid()
            }
        else:
            summary['local'] = {'status': 'idle'}

        # GitHub Actions status
        github_token = os.getenv('GITHUB_TOKEN', '')
        if github_token:
            try:
                repo = os.getenv('GITHUB_REPO', 'mostafazog/MRO-Supply')
                url = f'https://api.github.com/repos/{repo}/actions/runs'
                headers = {
                    'Authorization': f'token {github_token}',
                    'Accept': 'application/vnd.github.v3+json'
                }
                response = requests.get(url, headers=headers, params={'per_page': 1}, timeout=10)

                if response.status_code == 200:
                    runs = response.json().get('workflow_runs', [])
                    if runs:
                        latest = runs[0]
                        summary['github'] = {
                            'status': latest['status'],
                            'conclusion': latest.get('conclusion'),
                            'name': latest['name'],
                            'run_id': latest['id'],
                            'url': latest['html_url']
                        }
            except Exception as e:
                logger.error(f"Error getting GitHub status: {e}")

        # Azure Functions status
        try:
            azure_url = os.getenv('AZURE_FUNCTION_URL', 'https://mrosupply-scraper-func.azurewebsites.net')
            response = requests.get(f'{azure_url}/api/health', timeout=10)

            if response.status_code == 200:
                summary['azure'] = {
                    'status': 'healthy',
                    'url': azure_url
                }
            else:
                summary['azure'] = {'status': 'unhealthy'}
        except Exception:
            summary['azure'] = {'status': 'unreachable'}

        return jsonify(summary)

    except Exception as e:
        logger.error(f"Error getting distributed summary: {e}")
        return jsonify({'error': str(e)}), 500


# ========== HELPER FUNCTIONS ==========

def get_scraper_pid():
    """Get the PID of the running scraper"""
    try:
        if SCRAPER_PID_FILE.exists():
            with open(SCRAPER_PID_FILE, 'r') as f:
                pid = int(f.read().strip())
            return pid if is_process_running(pid) else None
    except Exception:
        return None
    return None


def is_process_running(pid):
    """Check if a process is running"""
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def is_scraper_running():
    """Check if scraper is currently running"""
    pid = get_scraper_pid()
    return bool(pid and is_process_running(pid))


def run_dashboard(config, host=None, port=None, debug=False):
    """Run the dashboard server"""
    if host is None:
        host = config.DASHBOARD_HOST

    init_dashboard(config)

    if port is None:
        port = config.DASHBOARD_PORT

    logger.info(f"Starting dashboard on {host}:{port}")
    print(f"\n{'=' * 60}")
    print(f"🌐 Dashboard starting on http://{host}:{port}")
    print(f"   Password: {config.DASHBOARD_PASSWORD}")
    print(f"{'=' * 60}\n")

    try:
        app.run(
            host=host,
            port=port,
            debug=debug,
            use_reloader=False
        )
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        raise


if __name__ == '__main__':
    import sys
    sys.path.insert(0, '.')
    from config import Config

    try:
        config = Config()

        print("Starting MRO Supply Scraper Dashboard")
        print("=" * 60)

        run_dashboard(
            config,
            port=config.DASHBOARD_PORT,
            debug=True
        )

    except KeyboardInterrupt:
        print("\nDashboard stopped")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
