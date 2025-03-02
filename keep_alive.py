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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('keep-alive')

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
    parser.add_argument('--url', type=str, default='http://localhost:8000/health',
                        help='URL to ping (default: http://localhost:8000/health)')
    parser.add_argument('--interval', type=int, default=240,
                        help='Ping interval in seconds (default: 240 seconds)')
    
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