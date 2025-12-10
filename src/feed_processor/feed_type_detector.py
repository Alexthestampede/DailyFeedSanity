"""
Feed type detection using AI (Ollama, LM Studio, etc.) for RSS Feed Processor
"""
import json
import os
from ..ai_client.base import BaseAIClient
from ..utils.logging_config import get_logger
from ..config import TEXT_MODEL, FEED_TYPE_CACHE_FILE, FEED_TYPE_DETECTION_TEMPERATURE

logger = get_logger(__name__)


class FeedTypeDetector:
    """
    Detect whether a feed is a comic or news feed using AI.
    Results are cached to avoid repeated analysis.
    """

    def __init__(self, ai_client=None, cache_file=None, model=None):
        """
        Initialize feed type detector.

        Args:
            ai_client: BaseAIClient instance (optional, will create default if not provided)
            cache_file: Path to cache file (default: from config.FEED_TYPE_CACHE_FILE)
            model: AI model to use for classification (optional, will load from user config or use default)
        """
        self.cache_file = cache_file or FEED_TYPE_CACHE_FILE
        self.cache = self._load_cache()

        # Use provided client or create default one
        if ai_client is None:
            from ..ai_client import create_ai_client_with_fallback
            logger.info("No AI client provided to FeedTypeDetector, creating default")
            ai_client, _, _ = create_ai_client_with_fallback()

        self.client = ai_client

        # Determine model: use provided model, or load from user config, or fall back to default
        if model is not None:
            self.model = model
        else:
            # Try to load model from user config (.config.json)
            self.model = self._get_model_from_config()

    def _get_model_from_config(self):
        """
        Get the text model from user configuration or fall back to default.

        Returns:
            Model name string
        """
        try:
            from ..utils.config_wizard import load_config
            user_config = load_config()
            if user_config and 'text_model' in user_config:
                model = user_config['text_model']
                logger.debug(f"Using text model from user config: {model}")
                return model
        except Exception as e:
            logger.debug(f"Could not load user config for model: {e}")

        # Fall back to default from config.py
        logger.debug(f"Using default text model: {TEXT_MODEL}")
        return TEXT_MODEL

    def _load_cache(self):
        """
        Load cached feed type classifications.

        Returns:
            dict with feed_url -> feed_type mappings
        """
        if not os.path.exists(self.cache_file):
            logger.debug(f"Cache file not found: {self.cache_file}")
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
        """
        Save feed type cache to disk.
        """
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
            logger.debug(f"Saved {len(self.cache)} feed types to cache")
        except Exception as e:
            logger.error(f"Failed to save cache to {self.cache_file}: {e}")

    def get_cached_type(self, feed_url):
        """
        Get cached feed type if available.

        Args:
            feed_url: URL of the feed

        Returns:
            'comic', 'news', or None if not cached
        """
        return self.cache.get(feed_url)

    def detect_feed_type(self, feed_data, feed_url):
        """
        Detect whether a feed is a comic or news feed using Ollama.

        Args:
            feed_data: Parsed feed data dict with 'entries' list
            feed_url: URL of the feed

        Returns:
            'comic' or 'news', or None if detection fails
        """
        # Check cache first
        cached = self.get_cached_type(feed_url)
        if cached:
            logger.info(f"Using cached feed type for {feed_url}: {cached}")
            return cached

        # Check AI availability
        if not self.client.health_check():
            logger.warning("AI server not available, cannot detect feed type")
            return None

        try:
            # Sample entries for analysis (up to 5)
            entries = feed_data.get('entries', [])[:5]

            if not entries:
                logger.warning(f"No entries to analyze for {feed_url}")
                return None

            # Build analysis prompt
            prompt = self._build_analysis_prompt(feed_data, entries)

            # Get classification from AI
            system_prompt = self._get_system_prompt()

            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                system=system_prompt,
                temperature=FEED_TYPE_DETECTION_TEMPERATURE
            )

            if not response:
                logger.error("AI returned no response for feed type detection")
                return None

            # Parse response
            feed_type = self._parse_response(response)

            if feed_type:
                # Cache the result
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
        """
        Build prompt for Ollama to analyze feed content.

        Args:
            feed_data: Parsed feed data
            entries: List of feed entries to analyze

        Returns:
            Prompt string
        """
        feed_title = feed_data.get('title', 'Unknown')

        prompt_parts = [
            f"Feed Title: {feed_title}",
            "",
            "Sample Entries:",
            ""
        ]

        for i, entry in enumerate(entries, 1):
            title = entry.get('title', 'Untitled')
            link = entry.get('link', '')
            description = entry.get('description', '')[:200]  # Limit description length

            prompt_parts.append(f"Entry {i}:")
            prompt_parts.append(f"  Title: {title}")
            prompt_parts.append(f"  URL: {link}")
            if description:
                prompt_parts.append(f"  Description: {description}...")
            prompt_parts.append("")

        prompt_parts.append("Based on this feed data, is this a comic/webcomic feed or a news/article feed?")

        return "\n".join(prompt_parts)

    def _get_system_prompt(self):
        """
        Get system prompt for feed type classification.

        Returns:
            System prompt string
        """
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
        """
        Parse Ollama response to extract feed type.

        Args:
            response: Response text from Ollama

        Returns:
            'comic', 'news', or None if parsing fails
        """
        # Clean and normalize response
        response = response.strip().lower()

        # Look for clear indicators
        if 'comic' in response and 'news' not in response:
            return 'comic'
        elif 'news' in response and 'comic' not in response:
            return 'news'
        else:
            # If response contains both or neither, try to extract first word
            first_word = response.split()[0] if response.split() else ''
            if first_word in ['comic', 'news']:
                return first_word
            return None

    def invalidate_cache_entry(self, feed_url):
        """
        Remove a feed from the cache (useful for re-classification).

        Args:
            feed_url: URL of the feed to remove from cache
        """
        if feed_url in self.cache:
            del self.cache[feed_url]
            self._save_cache()
            logger.info(f"Removed {feed_url} from cache")

    def clear_cache(self):
        """
        Clear all cached feed type classifications.
        """
        self.cache = {}
        self._save_cache()
        logger.info("Cleared feed type cache")
