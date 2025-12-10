"""
Feed language detection using AI for RSS Feed Processor
"""
import json
import os
from urllib.parse import urlparse
from ..ai_client.base import BaseAIClient
from ..utils.logging_config import get_logger
from ..config import TEXT_MODEL, FEED_LANGUAGE_CACHE_FILE, FEED_LANGUAGE_OVERRIDE_FILE, FEED_LANGUAGE_DETECTION_TEMPERATURE

logger = get_logger(__name__)


class FeedLanguageDetector:
    """
    Detect the language of a feed using AI.
    Results are cached by domain to avoid repeated analysis.
    Manual overrides take highest priority.
    """

    def __init__(self, ai_client=None, cache_file=None, override_file=None, model=None):
        """
        Initialize feed language detector.

        Args:
            ai_client: BaseAIClient instance (optional, will create default if not provided)
            cache_file: Path to cache file (default: from config.FEED_LANGUAGE_CACHE_FILE)
            override_file: Path to override file (default: from config.FEED_LANGUAGE_OVERRIDE_FILE)
            model: AI model to use for language detection (optional, will load from user config or use default)
        """
        self.cache_file = cache_file or FEED_LANGUAGE_CACHE_FILE
        self.override_file = override_file or FEED_LANGUAGE_OVERRIDE_FILE
        self.cache = self._load_cache()
        self.overrides = self._load_overrides()

        # Use provided client or create default one
        if ai_client is None:
            from ..ai_client import create_ai_client_with_fallback
            logger.info("No AI client provided to FeedLanguageDetector, creating default")
            ai_client, _, _ = create_ai_client_with_fallback()

        self.client = ai_client

        # Determine model: use provided model, or load from user config, or fall back to default
        if model is not None:
            self.model = model
        else:
            # Try to load model from user config (.config.json)
            self.model = self._get_model_from_config()

    def _load_cache(self):
        """
        Load cached feed language classifications.

        Returns:
            dict with domain -> language mappings
        """
        if not os.path.exists(self.cache_file):
            logger.debug(f"Language cache file not found: {self.cache_file}")
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
        """
        Save feed language cache to disk.
        """
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
            logger.debug(f"Saved {len(self.cache)} feed languages to cache")
        except Exception as e:
            logger.error(f"Failed to save language cache to {self.cache_file}: {e}")

    def _load_overrides(self):
        """
        Load manual language overrides from file.

        Returns:
            dict with domain -> language mappings
        """
        if not os.path.exists(self.override_file):
            logger.debug(f"Language override file not found: {self.override_file}")
            return {}

        overrides = {}
        try:
            with open(self.override_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()

                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue

                    # Parse: domain_or_url = language
                    if '=' not in line:
                        logger.warning(f"Invalid override format at line {line_num}: {line}")
                        continue

                    parts = line.split('=', 1)
                    if len(parts) != 2:
                        logger.warning(f"Invalid override format at line {line_num}: {line}")
                        continue

                    domain_or_url = parts[0].strip()
                    language = parts[1].strip()

                    # Extract domain if full URL provided
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

    def _extract_domain(self, feed_url):
        """
        Extract domain from feed URL for caching.

        Args:
            feed_url: Feed URL

        Returns:
            Domain string (e.g., "macitynet.it")
        """
        try:
            parsed = urlparse(feed_url)
            domain = parsed.netloc

            # Remove www. prefix if present
            if domain.startswith('www.'):
                domain = domain[4:]

            return domain
        except Exception as e:
            logger.error(f"Failed to extract domain from {feed_url}: {e}")
            return feed_url  # Fallback to full URL

    def get_feed_language(self, feed_url, feed_data=None):
        """
        Get the language for a feed using priority order:
        1. Manual overrides
        2. Cache
        3. AI detection
        4. Default to "English"

        Args:
            feed_url: URL of the feed
            feed_data: Optional parsed feed data for AI detection

        Returns:
            Language name (e.g., "English", "Italian", "Spanish")
        """
        domain = self._extract_domain(feed_url)

        # Priority 1: Check manual overrides
        if domain in self.overrides:
            language = self.overrides[domain]
            logger.info(f"Feed {domain} language from override: {language}")
            return language

        # Priority 2: Check cache
        if domain in self.cache:
            language = self.cache[domain]
            logger.info(f"Feed {domain} language from cache: {language}")
            return language

        # Priority 3: AI detection
        if feed_data:
            language = self.detect_feed_language(feed_url, feed_data)
            if language:
                # Cache the result
                self.cache[domain] = language
                self._save_cache()
                logger.info(f"Feed {domain} language detected via AI: {language}")
                return language

        # Priority 4: Default
        logger.info(f"Feed {domain} language defaulting to English")
        return "English"

    def detect_feed_language(self, feed_url, feed_data):
        """
        Detect the language of a feed using AI by sampling article titles/descriptions.

        Args:
            feed_url: URL of the feed
            feed_data: Parsed feed data dict with 'entries' list

        Returns:
            Language name (e.g., "English", "Italian") or None if detection fails
        """
        domain = self._extract_domain(feed_url)

        # Check AI availability
        if not self.client.health_check():
            logger.warning("AI server not available, cannot detect feed language")
            return None

        try:
            # Sample 2-3 entries for analysis
            entries = feed_data.get('entries', [])[:3]

            if not entries:
                logger.warning(f"No entries to analyze for language detection: {feed_url}")
                return None

            # Build analysis prompt
            prompt = self._build_analysis_prompt(feed_data, entries)

            # Get language from AI
            system_prompt = self._get_system_prompt()

            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                system=system_prompt,
                temperature=FEED_LANGUAGE_DETECTION_TEMPERATURE
            )

            if not response:
                logger.error("AI returned no response for language detection")
                return None

            # Parse response
            language = self._parse_response(response)

            if language:
                logger.info(f"Detected language for {domain}: {language}")
            else:
                logger.warning(f"Could not determine language from response: {response}")

            return language

        except Exception as e:
            logger.error(f"Error detecting language for {feed_url}: {e}")
            return None

    def _build_analysis_prompt(self, feed_data, entries):
        """
        Build prompt for AI to analyze feed content and detect language.

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
            description = entry.get('description', '')[:200]  # Limit description length

            prompt_parts.append(f"Entry {i}:")
            prompt_parts.append(f"  Title: {title}")
            if description:
                prompt_parts.append(f"  Description: {description}...")
            prompt_parts.append("")

        prompt_parts.append("Based on these feed entries, what language are they written in?")

        return "\n".join(prompt_parts)

    def _get_system_prompt(self):
        """
        Get system prompt for language detection.

        Returns:
            System prompt string
        """
        return (
            "You are a language detection expert. "
            "Analyze the provided feed content and determine what language it is written in.\n\n"
            "Respond with ONLY the language name in English (e.g., 'English', 'Italian', 'Spanish', "
            "'French', 'German', 'Portuguese', 'Japanese', 'Chinese', 'Korean', etc.).\n\n"
            "Do not provide explanations or additional text. Just the language name."
        )

    def _parse_response(self, response):
        """
        Parse AI response to extract language name.

        Args:
            response: Response text from AI

        Returns:
            Language name or None if parsing fails
        """
        # Clean and normalize response
        language = response.strip().strip('"\'.,')

        # Validate it's a reasonable response (not too long)
        if len(language) > 50:
            logger.warning(f"Unexpected language detection response: {language[:50]}...")
            return None

        # Capitalize first letter for consistency
        language = language.capitalize()

        return language

    def invalidate_cache_entry(self, feed_url):
        """
        Remove a feed from the cache (useful for re-detection).

        Args:
            feed_url: URL of the feed to remove from cache
        """
        domain = self._extract_domain(feed_url)
        if domain in self.cache:
            del self.cache[domain]
            self._save_cache()
            logger.info(f"Removed {domain} from language cache")

    def clear_cache(self):
        """
        Clear all cached feed language classifications.
        """
        self.cache = {}
        self._save_cache()
        logger.info("Cleared language cache")

    def add_override(self, feed_url, language):
        """
        Add a manual override for a feed's language.

        Args:
            feed_url: URL of the feed
            language: Language name (e.g., "Italian")
        """
        domain = self._extract_domain(feed_url)
        self.overrides[domain] = language
        logger.info(f"Added language override: {domain} = {language}")
