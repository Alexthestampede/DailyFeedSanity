"""
Feed type detection using AI for RSS Feed Processor.

Uses the text processor's generate() method to classify feeds as comic or news.
"""
import json
import os
from ..utils.logging_config import get_logger
from ..config import FEED_TYPE_CACHE_FILE, FEED_TYPE_DETECTION_TEMPERATURE

logger = get_logger(__name__)


class FeedTypeDetector:
    """
    Detect whether a feed is a comic or news feed using AI.
    Results are cached to avoid repeated analysis.
    """

    def __init__(self, text_processor=None, ai_client=None, cache_file=None):
        """
        Initialize feed type detector.

        Args:
            text_processor: Text processor with generate() method (preferred)
            ai_client: BaseAIClient instance (legacy - used for health_check only)
            cache_file: Path to cache file (default: from config)
        """
        self.cache_file = cache_file or FEED_TYPE_CACHE_FILE
        self.cache = self._load_cache()

        # Store text processor and client
        if text_processor is not None:
            self.text_processor = text_processor
        else:
            # Fallback: create from factory
            from ..ai_client import create_ai_client_with_fallback
            logger.info("No text processor provided to FeedTypeDetector, creating default")
            client, text_proc, _ = create_ai_client_with_fallback()
            self.text_processor = text_proc
            if ai_client is None:
                ai_client = client

        self.client = ai_client  # Used for health_check

    def _load_cache(self):
        """Load cached feed type classifications."""
        if not os.path.exists(self.cache_file):
            return {}
        try:
            with open(self.cache_file, 'r') as f:
                cache = json.load(f)
            logger.info(f"Loaded {len(cache)} feed types from cache")
            return cache
        except Exception as e:
            logger.error(f"Failed to load cache from {self.cache_file}: {e}")
            return {}

    def _save_cache(self):
        """Save feed type cache to disk."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
            logger.debug(f"Saved {len(self.cache)} feed types to cache")
        except Exception as e:
            logger.error(f"Failed to save cache to {self.cache_file}: {e}")

    def get_cached_type(self, feed_url):
        """Get cached feed type if available."""
        return self.cache.get(feed_url)

    def detect_feed_type(self, feed_data, feed_url):
        """
        Detect whether a feed is a comic or news feed using AI.

        Args:
            feed_data: Parsed feed data dict with 'entries' list
            feed_url: URL of the feed

        Returns:
            'comic' or 'news', or None if detection fails
        """
        cached = self.get_cached_type(feed_url)
        if cached:
            logger.info(f"Using cached feed type for {feed_url}: {cached}")
            return cached

        # Check AI availability if client is available
        if self.client and hasattr(self.client, 'health_check'):
            if not self.client.health_check():
                logger.warning("AI server not available, cannot detect feed type")
                return None

        try:
            entries = feed_data.get('entries', [])[:5]
            if not entries:
                logger.warning(f"No entries to analyze for {feed_url}")
                return None

            prompt = self._build_analysis_prompt(feed_data, entries)
            system_prompt = self._get_system_prompt()

            response = self.text_processor.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=FEED_TYPE_DETECTION_TEMPERATURE
            )

            if not response:
                logger.error("AI returned no response for feed type detection")
                return None

            feed_type = self._parse_response(response)

            if feed_type:
                self.cache[feed_url] = feed_type
                self._save_cache()
                logger.info(f"Detected feed type for {feed_url}: {feed_type}")
            else:
                logger.warning(f"Could not determine feed type from response: {response}")

            return feed_type

        except Exception as e:
            logger.error(f"Error detecting feed type for {feed_url}: {e}")
            return None

    def _build_analysis_prompt(self, feed_data, entries):
        """Build prompt for AI to analyze feed content."""
        feed_title = feed_data.get('title', 'Unknown')
        prompt_parts = [f"Feed Title: {feed_title}", "", "Sample Entries:", ""]

        for i, entry in enumerate(entries, 1):
            title = entry.get('title', 'Untitled')
            link = entry.get('link', '')
            description = entry.get('description', '')[:200]
            prompt_parts.append(f"Entry {i}:")
            prompt_parts.append(f"  Title: {title}")
            prompt_parts.append(f"  URL: {link}")
            if description:
                prompt_parts.append(f"  Description: {description}...")
            prompt_parts.append("")

        prompt_parts.append("Based on this feed data, is this a comic/webcomic feed or a news/article feed?")
        return "\n".join(prompt_parts)

    def _get_system_prompt(self):
        """Get system prompt for feed type classification."""
        return (
            "You are a feed classifier. Analyze RSS feed content and determine if it is a COMIC feed or NEWS feed.\n\n"
            "COMIC feeds:\n"
            "- Contain webcomics, comic strips, or visual storytelling\n"
            "- Entries typically link to comic pages with images\n"
            "- Titles are often simple or episodic (e.g., numbered, dated)\n"
            "- Descriptions may contain image tags or be minimal\n"
            "- URLs often contain patterns like /comic/, /comics/, numbered episodes\n\n"
            "NEWS feeds:\n"
            "- Contain news articles, blog posts, or text-heavy content\n"
            "- Entries are article headlines and summaries\n"
            "- Titles are descriptive article headlines\n"
            "- Descriptions contain article text or summaries\n"
            "- URLs typically point to article pages with /post/, /article/, /news/, dates\n\n"
            "Respond with ONLY one word: either 'comic' or 'news'. Do not provide explanations or additional text."
        )

    def _parse_response(self, response):
        """Parse AI response to extract feed type."""
        response = response.strip().lower()
        if 'comic' in response and 'news' not in response:
            return 'comic'
        elif 'news' in response and 'comic' not in response:
            return 'news'
        else:
            first_word = response.split()[0] if response.split() else ''
            if first_word in ['comic', 'news']:
                return first_word
            return None

    def invalidate_cache_entry(self, feed_url):
        """Remove a feed from the cache."""
        if feed_url in self.cache:
            del self.cache[feed_url]
            self._save_cache()
            logger.info(f"Removed {feed_url} from cache")

    def clear_cache(self):
        """Clear all cached feed type classifications."""
        self.cache = {}
        self._save_cache()
        logger.info("Cleared feed type cache")
