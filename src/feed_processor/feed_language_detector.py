"""
Feed language detection using AI for RSS Feed Processor.

Uses the text processor's generate() method to detect feed language.
"""
import json
import os
from urllib.parse import urlparse
from ..utils.logging_config import get_logger
from ..config import FEED_LANGUAGE_CACHE_FILE, FEED_LANGUAGE_OVERRIDE_FILE, FEED_LANGUAGE_DETECTION_TEMPERATURE

logger = get_logger(__name__)


class FeedLanguageDetector:
    """
    Detect the language of a feed using AI.
    Results are cached by domain to avoid repeated analysis.
    Manual overrides take highest priority.
    """

    def __init__(self, text_processor=None, ai_client=None, cache_file=None, override_file=None):
        """
        Initialize feed language detector.

        Args:
            text_processor: Text processor with generate() method (preferred)
            ai_client: BaseAIClient instance (legacy - used for health_check only)
            cache_file: Path to cache file
            override_file: Path to override file
        """
        self.cache_file = cache_file or FEED_LANGUAGE_CACHE_FILE
        self.override_file = override_file or FEED_LANGUAGE_OVERRIDE_FILE
        self.cache = self._load_cache()
        self.overrides = self._load_overrides()

        if text_processor is not None:
            self.text_processor = text_processor
        else:
            from ..ai_client import create_ai_client_with_fallback
            logger.info("No text processor provided to FeedLanguageDetector, creating default")
            client, text_proc, _ = create_ai_client_with_fallback()
            self.text_processor = text_proc
            if ai_client is None:
                ai_client = client

        self.client = ai_client  # Used for health_check

    def _load_cache(self):
        """Load cached feed language classifications."""
        if not os.path.exists(self.cache_file):
            return {}
        try:
            with open(self.cache_file, 'r') as f:
                cache = json.load(f)
            logger.info(f"Loaded {len(cache)} feed languages from cache")
            return cache
        except Exception as e:
            logger.error(f"Failed to load language cache from {self.cache_file}: {e}")
            return {}

    def _save_cache(self):
        """Save feed language cache to disk."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
            logger.debug(f"Saved {len(self.cache)} feed languages to cache")
        except Exception as e:
            logger.error(f"Failed to save language cache to {self.cache_file}: {e}")

    def _load_overrides(self):
        """Load manual language overrides from file."""
        if not os.path.exists(self.override_file):
            return {}

        overrides = {}
        try:
            with open(self.override_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' not in line:
                        logger.warning(f"Invalid override format at line {line_num}: {line}")
                        continue
                    parts = line.split('=', 1)
                    if len(parts) != 2:
                        continue
                    domain_or_url = parts[0].strip()
                    language = parts[1].strip()
                    if domain_or_url.startswith('http'):
                        domain = self._extract_domain(domain_or_url)
                    else:
                        domain = domain_or_url
                    overrides[domain] = language
                    logger.debug(f"Loaded language override: {domain} = {language}")

            logger.info(f"Loaded {len(overrides)} language overrides from {self.override_file}")
            return overrides
        except Exception as e:
            logger.error(f"Failed to load language overrides from {self.override_file}: {e}")
            return {}

    def _extract_domain(self, feed_url):
        """Extract domain from feed URL for caching."""
        try:
            parsed = urlparse(feed_url)
            domain = parsed.netloc
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except Exception as e:
            logger.error(f"Failed to extract domain from {feed_url}: {e}")
            return feed_url

    def get_feed_language(self, feed_url, feed_data=None):
        """
        Get the language for a feed using priority order:
        1. Manual overrides
        2. Cache
        3. AI detection
        4. Default to "English"
        """
        domain = self._extract_domain(feed_url)

        if domain in self.overrides:
            language = self.overrides[domain]
            logger.info(f"Feed {domain} language from override: {language}")
            return language

        if domain in self.cache:
            language = self.cache[domain]
            logger.info(f"Feed {domain} language from cache: {language}")
            return language

        if feed_data:
            language = self.detect_feed_language(feed_url, feed_data)
            if language:
                self.cache[domain] = language
                self._save_cache()
                logger.info(f"Feed {domain} language detected via AI: {language}")
                return language

        logger.info(f"Feed {domain} language defaulting to English")
        return "English"

    def detect_feed_language(self, feed_url, feed_data):
        """
        Detect the language of a feed using AI.

        Args:
            feed_url: URL of the feed
            feed_data: Parsed feed data dict with 'entries' list

        Returns:
            Language name or None if detection fails
        """
        # Check AI availability if client is available
        if self.client and hasattr(self.client, 'health_check'):
            if not self.client.health_check():
                logger.warning("AI server not available, cannot detect feed language")
                return None

        try:
            entries = feed_data.get('entries', [])[:3]
            if not entries:
                logger.warning(f"No entries to analyze for language detection: {feed_url}")
                return None

            prompt = self._build_analysis_prompt(feed_data, entries)
            system_prompt = self._get_system_prompt()

            response = self.text_processor.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=FEED_LANGUAGE_DETECTION_TEMPERATURE
            )

            if not response:
                logger.error("AI returned no response for language detection")
                return None

            language = self._parse_response(response)
            if language:
                logger.info(f"Detected language for {self._extract_domain(feed_url)}: {language}")
            else:
                logger.warning(f"Could not determine language from response: {response}")
            return language

        except Exception as e:
            logger.error(f"Error detecting language for {feed_url}: {e}")
            return None

    def _build_analysis_prompt(self, feed_data, entries):
        """Build prompt for AI to analyze feed content and detect language."""
        feed_title = feed_data.get('title', 'Unknown')
        prompt_parts = [f"Feed Title: {feed_title}", "", "Sample Entries:", ""]

        for i, entry in enumerate(entries, 1):
            title = entry.get('title', 'Untitled')
            description = entry.get('description', '')[:200]
            prompt_parts.append(f"Entry {i}:")
            prompt_parts.append(f"  Title: {title}")
            if description:
                prompt_parts.append(f"  Description: {description}...")
            prompt_parts.append("")

        prompt_parts.append("Based on these feed entries, what language are they written in?")
        return "\n".join(prompt_parts)

    def _get_system_prompt(self):
        """Get system prompt for language detection."""
        return (
            "You are a language detection expert. "
            "Analyze the provided feed content and determine what language it is written in.\n\n"
            "Respond with ONLY the language name in English (e.g., 'English', 'Italian', 'Spanish', "
            "'French', 'German', 'Portuguese', 'Japanese', 'Chinese', 'Korean', etc.).\n\n"
            "Do not provide explanations or additional text. Just the language name."
        )

    def _parse_response(self, response):
        """Parse AI response to extract language name."""
        language = response.strip().strip('"\'.,')
        if len(language) > 50:
            logger.warning(f"Unexpected language detection response: {language[:50]}...")
            return None
        language = language.capitalize()
        return language

    def invalidate_cache_entry(self, feed_url):
        """Remove a feed from the cache."""
        domain = self._extract_domain(feed_url)
        if domain in self.cache:
            del self.cache[domain]
            self._save_cache()
            logger.info(f"Removed {domain} from language cache")

    def clear_cache(self):
        """Clear all cached feed language classifications."""
        self.cache = {}
        self._save_cache()
        logger.info("Cleared language cache")

    def add_override(self, feed_url, language):
        """Add a manual override for a feed's language."""
        domain = self._extract_domain(feed_url)
        self.overrides[domain] = language
        logger.info(f"Added language override: {domain} = {language}")
