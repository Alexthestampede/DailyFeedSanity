"""
HTTP client utilities for RSS Feed Processor
"""
import json
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from pathlib import Path
from .logging_config import get_logger
from ..config import (
    USER_AGENT,
    REQUEST_TIMEOUT,
    MAX_RETRIES,
    RETRY_DELAY,
    RETRY_BACKOFF
)

logger = get_logger(__name__)

_CONFIG_FILE = Path(__file__).parent.parent.parent / '.config.json'


def get_configured_request_timeout():
    """
    Get the user-configured request timeout from .config.json.

    Returns:
        Timeout in seconds (falls back to src config default)
    """
    try:
        if _CONFIG_FILE.exists():
            with open(_CONFIG_FILE, 'r') as f:
                config = json.load(f)
            value = config.get('request_timeout')
            if value is not None:
                timeout = int(value)
                if timeout > 0:
                    return timeout
                logger.warning(f"Invalid request_timeout in config: {value}, using default")
    except (json.JSONDecodeError, OSError, TypeError, ValueError) as e:
        logger.warning(f"Could not load request_timeout from config: {e}")
    return REQUEST_TIMEOUT


def create_session(max_retries=MAX_RETRIES):
    """
    Create a requests session with retry logic and proper headers.

    Args:
        max_retries: Maximum number of retries

    Returns:
        requests.Session object
    """
    session = requests.Session()

    # Set default headers
    session.headers.update({
        'User-Agent': USER_AGENT,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    })

    # Configure retries with backoff
    retry_strategy = Retry(
        total=max_retries,
        backoff_factor=RETRY_BACKOFF,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


def fetch_url(url, session=None, timeout=None, **kwargs):
    """
    Fetch a URL with retry logic and error handling.

    Args:
        url: URL to fetch
        session: requests.Session object (creates one if None)
        timeout: Request timeout in seconds
        **kwargs: Additional arguments to pass to requests.get()

    Returns:
        requests.Response object

    Raises:
        requests.exceptions.RequestException: On failure after retries
    """
    if session is None:
        session = create_session()

    if timeout is None:
        timeout = get_configured_request_timeout()

    attempt = 0
    last_exception = None

    while attempt < MAX_RETRIES:
        try:
            logger.debug(f"Fetching URL (attempt {attempt + 1}/{MAX_RETRIES}): {url}")
            response = session.get(url, timeout=timeout, **kwargs)
            response.raise_for_status()
            logger.debug(f"Successfully fetched: {url}")
            return response

        except requests.exceptions.RequestException as e:
            last_exception = e
            attempt += 1

            if attempt < MAX_RETRIES:
                sleep_time = RETRY_DELAY * (RETRY_BACKOFF ** (attempt - 1))
                logger.warning(f"Request failed: {e}. Retrying in {sleep_time}s...")
                time.sleep(sleep_time)
            else:
                logger.error(f"Failed to fetch URL after {MAX_RETRIES} attempts: {url}")

    raise last_exception


def download_file(url, output_path, session=None, timeout=None, **kwargs):
    """
    Download a file from URL and save to disk.

    Args:
        url: URL to download
        output_path: Path to save file
        session: requests.Session object (creates one if None)
        timeout: Request timeout in seconds

    Returns:
        True if successful, False otherwise
    """
    try:
        response = fetch_url(url, session=session, timeout=timeout, stream=True)

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        logger.info(f"Downloaded file: {url} -> {output_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to download file {url}: {e}")
        return False


def fetch_with_custom_retry(url, retry_count=3, delay=2, session=None):
    """
    Fetch URL with custom retry logic (more flexible than session retries).

    Args:
        url: URL to fetch
        retry_count: Number of retries
        delay: Base delay between retries
        session: requests.Session object

    Returns:
        requests.Response object or None
    """
    if session is None:
        session = create_session()

    for attempt in range(retry_count):
        try:
            response = session.get(url, timeout=get_configured_request_timeout())
            response.raise_for_status()
            return response

        except requests.exceptions.RequestException as e:
            if attempt < retry_count - 1:
                sleep_time = delay * (RETRY_BACKOFF ** attempt)
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}. Retrying in {sleep_time}s...")
                time.sleep(sleep_time)
            else:
                logger.error(f"All {retry_count} attempts failed for {url}: {e}")
                return None

    return None
