"""
Configuration for the 1point3acres scraper.
"""
import os

BASE_URL = "https://www.1point3acres.com"
LOGIN_URL = f"{BASE_URL}/api/users/login"
INTERVIEW_BASE_URL = f"{BASE_URL}/interview"

DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0'
}

def get_auth_credentials():
    """Get authentication credentials from environment variables."""
    return {
        'username': os.environ.get('ONEPOINT3ACRES_USERNAME', ''),
        'password': os.environ.get('ONEPOINT3ACRES_PASSWORD', '')
    }

OUTPUT_DIR = "output"
THREAD_OUTPUT_FILE = "1point3acres_threads.txt"

REQUEST_TIMEOUT = 30  # seconds
RETRY_COUNT = 3
RETRY_DELAY = 2  # seconds
