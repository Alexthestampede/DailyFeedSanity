"""
Feed classification utilities for RSS Feed Processor
"""
import os
from urllib.parse import urlparse
from ..utils.logging_config import get_logger
from ..config import FEED_TYPES, SPECIAL_HANDLERS, FEED_TYPE_OVERRIDES_FILE
from .feed_type_detector import FeedTypeDetector

logger = get_logger(__name__)


class FeedClassifier:
    """
    Classify feeds as comic or news based on domain.
    Uses AI (Ollama, LM Studio, etc.) for automatic detection of unknown feeds.
    """

    def __init__(self, use_ai_detection=True, ai_client=None):
        """
        Initialize feed classifier.

        Args:
            use_ai_detection: Whether to use AI for unknown feeds (default: True)
            ai_client: BaseAIClient instance to use (optional, will be created if needed)
        """
        self.use_ai_detection = use_ai_detection
        self.feed_detector = None

        if use_ai_detection:
            # Pass ai_client to FeedTypeDetector if provided
            self.feed_detector = FeedTypeDetector(ai_client=ai_client)

        self.manual_overrides = self._load_manual_overrides()

    def classify_feed(self, feed_url, feed_data=None):
        """
        Classify a feed URL as 'comic' or 'news'.

        Priority order:
        1. Manual overrides (feed_type_overrides.txt) - HIGHEST PRIORITY
        2. Explicit FEED_TYPES config (hardcoded)
        3. Cache
        4. Ollama detection
        5. Default to 'comic' (fallback)

        Args:
            feed_url: URL of the feed
            feed_data: Parsed feed data (optional, for Ollama detection)

        Returns:
            'comic' or 'news'
        """
        domain = self._extract_domain(feed_url)

        # Priority 1: Check manual overrides first (user always right!)
        if feed_url in self.manual_overrides:
            feed_type = self.manual_overrides[feed_url]
            logger.info(f"Classified {feed_url} as {feed_type} (manual override)")
            return feed_type

        # Priority 2: Check against explicit configuration in FEED_TYPES
        for known_domain, feed_type in FEED_TYPES.items():
            if known_domain in domain:
                logger.debug(f"Classified {feed_url} as {feed_type} (matched {known_domain})")
                return feed_type

        # Priority 3: Check cache
        if self.feed_detector:
            cached_type = self.feed_detector.get_cached_type(feed_url)
            if cached_type:
                logger.info(f"Classified {feed_url} as {cached_type} (from cache)")
                return cached_type

        # Priority 4: Use AI detection if feed_data is available
        if self.use_ai_detection and self.feed_detector and feed_data:
            logger.info(f"Unknown feed {feed_url}, using AI for detection")
            detected_type = self.feed_detector.detect_feed_type(feed_data, feed_url)
            if detected_type:
                logger.info(f"Classified {feed_url} as '{detected_type}' (AI detection). "
                           f"To override, add to feed_type_overrides.txt: {feed_url} = comic|news")
                return detected_type
            else:
                logger.warning(f"AI detection failed for {feed_url}, using default")

        # Priority 5: Default to comic (safer assumption for this use case)
        logger.debug(f"Classified {feed_url} as comic (default)")
        return 'comic'

    def get_special_handler(self, feed_url):
        """
        Get special handler name for a feed if it requires one.

        Args:
            feed_url: URL of the feed

        Returns:
            Handler name string, or None if no special handler needed
        """
        domain = self._extract_domain(feed_url)

        for special_domain, handler_name in SPECIAL_HANDLERS.items():
            if special_domain in domain:
                logger.debug(f"Found special handler for {feed_url}: {handler_name}")
                return handler_name

        return None

    def _extract_domain(self, url):
        """
        Extract domain from URL.

        Args:
            url: URL string

        Returns:
            Domain string
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]

            return domain

        except Exception as e:
            logger.error(f"Error extracting domain from {url}: {e}")
            return ""

    def get_feed_name(self, feed_url):
        """
        Extract a friendly name from feed URL.

        Args:
            feed_url: URL of the feed

        Returns:
            Friendly name string
        """
        domain = self._extract_domain(feed_url)

        # Remove common suffixes
        name = domain.replace('.com', '').replace('.net', '').replace('.it', '').replace('.org', '')

        # Capitalize first letter of each word
        name = ' '.join(word.capitalize() for word in name.replace('-', ' ').replace('_', ' ').split())

        return name

    def _load_manual_overrides(self):
        """
        Load manual feed type overrides from feed_type_overrides.txt.

        Returns:
            dict mapping feed_url -> feed_type
        """
        overrides = {}

        if not os.path.exists(FEED_TYPE_OVERRIDES_FILE):
            logger.debug(f"No manual overrides file found at {FEED_TYPE_OVERRIDES_FILE}")
            return overrides

        try:
            with open(FEED_TYPE_OVERRIDES_FILE, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    # Strip whitespace
                    line = line.strip()

                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue

                    # Parse line: feed_url = type
                    if '=' not in line:
                        logger.warning(f"Invalid override at line {line_num}: missing '=' separator: {line}")
                        continue

                    parts = line.split('=', 1)
                    if len(parts) != 2:
                        logger.warning(f"Invalid override at line {line_num}: {line}")
                        continue

                    feed_url = parts[0].strip()
                    feed_type = parts[1].strip().lower()

                    # Validate feed type
                    if feed_type not in ['comic', 'news']:
                        logger.warning(f"Invalid feed type at line {line_num}: '{feed_type}' (must be 'comic' or 'news')")
                        continue

                    # Validate URL (basic check)
                    if not feed_url.startswith('http'):
                        logger.warning(f"Invalid URL at line {line_num}: {feed_url} (must start with http/https)")
                        continue

                    overrides[feed_url] = feed_type
                    logger.debug(f"Loaded manual override: {feed_url} = {feed_type}")

            if overrides:
                logger.info(f"Loaded {len(overrides)} manual feed type override(s) from {FEED_TYPE_OVERRIDES_FILE}")
            else:
                logger.debug(f"No valid overrides found in {FEED_TYPE_OVERRIDES_FILE}")

        except Exception as e:
            logger.error(f"Error loading manual overrides from {FEED_TYPE_OVERRIDES_FILE}: {e}")

        return overrides
