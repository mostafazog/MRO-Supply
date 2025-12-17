"""
Azure Functions - Distributed Web Scraper
HTTP-triggered function that scrapes a batch of URLs
"""

import json
import logging
import time
import os
import azure.functions as func
from typing import List, Dict

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    # Will be installed via requirements.txt
    pass

app = func.FunctionApp()

# Configuration from environment variables
PROXY_HOST = os.getenv('PROXY_HOST', 'p.webshare.io')
PROXY_PORT = os.getenv('PROXY_PORT', '10000')
PROXY_USER = os.getenv('PROXY_USER')
PROXY_PASS = os.getenv('PROXY_PASS')


def get_proxy_url() -> str:
    """Get proxy URL from environment"""
    if all([PROXY_USER, PROXY_PASS, PROXY_HOST, PROXY_PORT]):
        return f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
    return None


def scrape_product(url: str) -> Dict:
    """
    Scrape a single product

    Args:
        url: Product URL to scrape

    Returns:
        Product data dict or None if failed
    """
    proxy_url = get_proxy_url()
    proxies = {'http': proxy_url, 'https': proxy_url} if proxy_url else None

    try:
        response = requests.get(
            url,
            proxies=proxies,
            timeout=30,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml',
                'Accept-Language': 'en-US,en;q=0.9',
            }
        )

        if response.status_code != 200:
            logging.warning(f"HTTP {response.status_code} for {url}")
            return {
                'url': url,
                'error': f'HTTP {response.status_code}',
                'success': False
            }

        # Parse HTML - use html.parser like main scraper
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract product data using same logic as main scraper
        product = {
            'url': url,
            'title': '',
            'sku': '',
            'price': '',
            'availability': '',
            'description': '',
            'specifications': [],
            'images': [],
            'category': '',
            'brand': '',
            'success': True,
            'scraped_at': time.time()
        }

        # Title - use first h1
        title_tag = soup.find('h1')
        if title_tag:
            product['title'] = title_tag.get_text(strip=True)

        # SKU - extract from URL
        url_parts = url.rstrip('/').split('/')
        if url_parts:
            last_part = url_parts[-1]
            if '_' in last_part:
                product['sku'] = last_part.split('_')[0]

        # Price
        price_tag = soup.find('p', class_='price')
        if price_tag:
            product['price'] = price_tag.get_text(strip=True)

        # Availability
        avail_div = soup.find('div', class_=lambda x: x and 'availability' in x.lower() if x else False)
        if avail_div:
            product['availability'] = avail_div.get_text(strip=True)

        # Description - from meta tag
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            product['description'] = meta_desc.get('content', '')

        # Brand - extract from URL
        if url_parts and '_' in url_parts[-1]:
            parts = url_parts[-1].split('_')
            if len(parts) >= 3:
                product['brand'] = parts[-1].replace('-', ' ').title()

        # Images
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src')
            if src and ('product' in src.lower() or 'static.mrosupply' in src):
                if 'icon' not in src and 'chevron' not in src:
                    product['images'].append(src)

        # Category - from URL path
        if len(url_parts) > 4:
            product['category'] = url_parts[3].replace('-', ' ').title()

        return product

    except Exception as e:
        logging.error(f"Error scraping {url}: {e}")
        return {
            'url': url,
            'error': str(e),
            'success': False
        }


def extract_text(soup, selector: str) -> str:
    """Extract text from CSS selector"""
    try:
        element = soup.select_one(selector)
        return element.get_text(strip=True) if element else ''
    except:
        return ''


def extract_images(soup) -> List[str]:
    """Extract image URLs"""
    try:
        images = []
        for img in soup.select('img.product-image'):
            src = img.get('src') or img.get('data-src')
            if src:
                images.append(src)
        return images
    except:
        return []


def extract_specs(soup) -> Dict:
    """Extract product specifications"""
    try:
        specs = {}
        for row in soup.select('table.specs tr'):
            cells = row.select('td')
            if len(cells) >= 2:
                key = cells[0].get_text(strip=True)
                value = cells[1].get_text(strip=True)
                specs[key] = value
        return specs
    except:
        return {}


@app.function_name(name="ScrapeBatch")
@app.route(route="scrape", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def scrape_batch(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP-triggered function to scrape a batch of URLs

    Request body:
    {
        "urls": ["url1", "url2", ...],
        "batch_id": 123
    }

    Response:
    {
        "batch_id": 123,
        "total": 10,
        "success": 8,
        "failed": 2,
        "products": [...],
        "errors": [...]
    }
    """
    logging.info('ScrapeBatch function triggered')

    try:
        # Parse request body
        req_body = req.get_json()
        urls = req_body.get('urls', [])
        batch_id = req_body.get('batch_id', 0)

        if not urls:
            return func.HttpResponse(
                json.dumps({"error": "No URLs provided"}),
                status_code=400,
                mimetype="application/json"
            )

        logging.info(f"Processing batch {batch_id} with {len(urls)} URLs")

        # Scrape all URLs
        products = []
        errors = []

        for url in urls:
            result = scrape_product(url)

            if result.get('success'):
                products.append(result)
            else:
                errors.append(result)

        # Build response
        response = {
            'batch_id': batch_id,
            'total': len(urls),
            'success': len(products),
            'failed': len(errors),
            'products': products,
            'errors': errors,
            'timestamp': time.time()
        }

        logging.info(
            f"Batch {batch_id} completed: "
            f"{len(products)} success, {len(errors)} failed"
        )

        return func.HttpResponse(
            json.dumps(response),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        logging.error(f"Function error: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )


@app.function_name(name="HealthCheck")
@app.route(route="health", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint"""
    return func.HttpResponse(
        json.dumps({
            "status": "healthy",
            "timestamp": time.time()
        }),
        status_code=200,
        mimetype="application/json"
    )


# Queue-triggered function for scalability
@app.function_name(name="ScrapeFromQueue")
@app.queue_trigger(arg_name="msg", queue_name="scrape-queue", connection="AzureWebJobsStorage")
@app.queue_output(arg_name="outputQueueItem", queue_name="results-queue", connection="AzureWebJobsStorage")
def scrape_from_queue(msg: func.QueueMessage, outputQueueItem: func.Out[str]) -> None:
    """
    Queue-triggered function for better scalability

    Message format:
    {
        "url": "https://...",
        "batch_id": 123
    }
    """
    logging.info('ScrapeFromQueue triggered')

    try:
        # Parse message
        message = json.loads(msg.get_body().decode('utf-8'))
        url = message.get('url')
        batch_id = message.get('batch_id', 0)

        if not url:
            logging.error("No URL in message")
            return

        # Scrape product
        result = scrape_product(url)
        result['batch_id'] = batch_id

        # Send to results queue
        outputQueueItem.set(json.dumps(result))

        logging.info(f"Scraped {url}: {'success' if result.get('success') else 'failed'}")

    except Exception as e:
        logging.error(f"Queue function error: {e}")


# Blob-triggered function for batch results
@app.function_name(name="AggregateBatchResults")
@app.blob_trigger(arg_name="blob", path="batches/{name}", connection="AzureWebJobsStorage")
def aggregate_batch(blob: func.InputStream) -> None:
    """
    Triggered when a batch result is uploaded to blob storage
    Can aggregate results, send notifications, etc.
    """
    logging.info(f'Blob trigger: {blob.name}')

    try:
        # Read batch data
        batch_data = json.loads(blob.read().decode('utf-8'))

        logging.info(
            f"Batch {batch_data.get('batch_id')} aggregated: "
            f"{batch_data.get('success')} products"
        )

        # Could send notification, update database, etc.

    except Exception as e:
        logging.error(f"Aggregation error: {e}")
