"""
Content cleaning utilities for news articles
"""
import re
from bs4 import BeautifulSoup
from ..utils.logging_config import get_logger
from ..config import MAX_ARTICLE_LENGTH

logger = get_logger(__name__)


class ContentCleaner:
    """
    Clean and normalize article content for processing.
    """

    def __init__(self):
        """
        Initialize content cleaner.
        """
        pass

    def clean_text(self, text, max_length=MAX_ARTICLE_LENGTH):
        """
        Clean and normalize article text.

        Args:
            text: Raw article text
            max_length: Maximum length in characters

        Returns:
            Cleaned text string
        """
        if not text:
            return ""

        # Remove HTML tags if any remain
        text = self._strip_html(text)

        # Normalize whitespace
        text = self._normalize_whitespace(text)

        # Remove boilerplate patterns
        text = self._remove_boilerplate(text)

        # Truncate if too long
        if len(text) > max_length:
            text = text[:max_length]
            # Try to end at sentence boundary
            last_period = text.rfind('.')
            if last_period > max_length * 0.8:  # Keep at least 80%
                text = text[:last_period + 1]

        return text.strip()

    def _strip_html(self, text):
        """
        Remove HTML tags from text.

        Args:
            text: Text with possible HTML

        Returns:
            Plain text
        """
        try:
            soup = BeautifulSoup(text, 'html.parser')
            return soup.get_text()
        except Exception:
            # Fallback: simple regex
            text = re.sub(r'<[^>]+>', '', text)
            return text

    def _normalize_whitespace(self, text):
        """
        Normalize whitespace in text.

        Args:
            text: Input text

        Returns:
            Normalized text
        """
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)

        # Replace multiple newlines with double newline
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)

        # Remove leading/trailing whitespace from lines
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)

        return text

    def _remove_boilerplate(self, text):
        """
        Remove common boilerplate patterns.

        Args:
            text: Input text

        Returns:
            Cleaned text
        """
        # Common boilerplate patterns
        boilerplate_patterns = [
            r'Click here to.*?(?:\n|$)',
            r'Subscribe to.*?(?:\n|$)',
            r'Follow us on.*?(?:\n|$)',
            r'Share this.*?(?:\n|$)',
            r'Advertisement\s*',
            r'Related Articles.*?(?:\n|$)',
            r'Read more.*?(?:\n|$)',
        ]

        for pattern in boilerplate_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        return text

    def clean_title(self, title):
        """
        Clean article title.

        Args:
            title: Raw title

        Returns:
            Cleaned title
        """
        if not title:
            return "Untitled"

        # Remove HTML entities
        title = self._strip_html(title)

        # Remove site name suffix (e.g., " - Site Name")
        title = re.sub(r'\s*[-|]\s*[^-|]+\s*$', '', title)

        # Clean whitespace
        title = ' '.join(title.split())

        return title.strip()

    def extract_summary_from_text(self, text, max_sentences=3):
        """
        Extract first few sentences as a basic summary.

        Args:
            text: Article text
            max_sentences: Maximum number of sentences

        Returns:
            Summary string
        """
        if not text:
            return ""

        # Split into sentences (basic)
        sentences = re.split(r'[.!?]+\s+', text)

        # Take first N sentences
        summary_sentences = sentences[:max_sentences]

        summary = '. '.join(summary_sentences)

        # Ensure it ends with period
        if not summary.endswith('.'):
            summary += '.'

        return summary

    def validate_article_content(self, text):
        """
        Validate that article has substantial content.

        Args:
            text: Article text

        Returns:
            dict with validation results
        """
        result = {
            'valid': False,
            'word_count': 0,
            'char_count': 0,
            'reason': None
        }

        if not text:
            result['reason'] = "Empty text"
            return result

        # Count words and characters
        words = text.split()
        result['word_count'] = len(words)
        result['char_count'] = len(text)

        # Minimum thresholds
        MIN_WORDS = 50
        MIN_CHARS = 200

        if result['word_count'] < MIN_WORDS:
            result['reason'] = f"Too few words: {result['word_count']} < {MIN_WORDS}"
            return result

        if result['char_count'] < MIN_CHARS:
            result['reason'] = f"Too few characters: {result['char_count']} < {MIN_CHARS}"
            return result

        result['valid'] = True
        return result
