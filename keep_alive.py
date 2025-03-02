#!/usr/bin/env python
"""
Keep-alive script for Steam Games Search API.

This script periodically pings the API's health endpoint to prevent
the server from going inactive after periods of no traffic.

Usage:
    python keep_alive.py [--url URL] [--interval SECONDS]

Example:
    python keep_alive.py --url https://your-api-url.com --interval 240
"""

import argparse
import logging
import time
import requests
import sys
from datetime import datetime
import asyncio
import aiohttp
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger('main')

# Get the API host from environment or default to localhost
is_render = os.getenv("RENDER", "false").lower() == "true"
port = os.getenv("PORT", "8000")  # Use the same port defined in .env

# If running on Render, use localhost with the correct port
if is_render:
    # On Render, services are available internally at localhost with the assigned PORT
    api_host = f"http://localhost:{port}"
else:
    # For local development or other environments
    api_host = os.getenv("API_HOST", f"http://localhost:{port}")

# URL to ping (health endpoint)
health_url = f"{api_host}/health"
logger.info(f"Keep-alive will ping: {health_url}")

# Add randomization to avoid all instances pinging at exactly the same time
jitter = 10  # seconds of random jitter

# Keep-alive interval in seconds (default: 4 minutes - less than Render's 5 min timeout)
interval = int(os.getenv("KEEPALIVE_INTERVAL", "240"))

def ping_server(url):
    """Ping the server and return the response status."""
    try:
        response = requests.get(url)
        return {
            'status_code': response.status_code,
            'response_time': response.elapsed.total_seconds()
        }
    except Exception as e:
        logger.error(f"Failed to ping server: {str(e)}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Keep-alive script for Steam Games Search API')
    parser.add_argument('--url', type=str, default=health_url,
                        help=f'URL to ping (default: {health_url})')
    parser.add_argument('--interval', type=int, default=interval,
                        help=f'Ping interval in seconds (default: {interval} seconds)')
    
    args = parser.parse_args()
    
    logger.info(f"Starting keep-alive service for {args.url}")
    logger.info(f"Ping interval: {args.interval} seconds")
    
    ping_count = 0
    
    try:
        while True:
            ping_count += 1
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            logger.info(f"Ping #{ping_count} at {now}")
            result = ping_server(args.url)
            
            if result:
                logger.info(f"Server responded with status code {result['status_code']} in {result['response_time']:.3f} seconds")
            
            time.sleep(args.interval)
    except KeyboardInterrupt:
        logger.info("Keep-alive service stopped by user")
    except Exception as e:
        logger.error(f"Keep-alive service stopped due to error: {str(e)}")

if __name__ == "__main__":
    main() 