"""
RSS feed parsing utilities for RSS Feed Processor
"""
import feedparser
import html
from datetime import datetime
from ..utils.logging_config import get_logger
from ..utils.http_client import fetch_url

logger = get_logger(__name__)


class FeedParser:
    """
    Parse RSS feeds and extract normalized data.
    """

    def __init__(self):
        """
        Initialize feed parser.
        """
        pass

    def parse_feed(self, feed_url, session=None):
        """
        Parse an RSS feed and return normalized data.

        Args:
            feed_url: URL of RSS feed
            session: requests.Session object

        Returns:
            dict with feed data, or None on error
        """
        logger.info(f"Parsing feed: {feed_url}")

        try:
            # Fetch feed content
            response = fetch_url(feed_url, session=session)
            feed_content = response.content

            # Parse with feedparser
            feed = feedparser.parse(feed_content)

            if feed.bozo:
                logger.warning(f"Feed has parsing issues: {feed_url}")

            # Extract feed metadata
            feed_data = {
                'url': feed_url,
                'title': self._get_feed_title(feed),
                'entries': []
            }

            # Parse entries
            for entry in feed.entries:
                entry_data = self._parse_entry(entry, feed_url)
                if entry_data:
                    feed_data['entries'].append(entry_data)

            logger.info(f"Parsed {len(feed_data['entries'])} entries from {feed_url}")
            return feed_data

        except Exception as e:
            logger.error(f"Failed to parse feed {feed_url}: {e}")
            return None

    def _get_feed_title(self, feed):
        """
        Extract feed title.

        Args:
            feed: feedparser feed object

        Returns:
            Feed title string
        """
        if hasattr(feed, 'feed') and hasattr(feed.feed, 'title'):
            return feed.feed.title
        return "Unknown Feed"

    def _parse_entry(self, entry, feed_url):
        """
        Parse a single feed entry.

        Args:
            entry: feedparser entry object
            feed_url: Original feed URL

        Returns:
            dict with entry data
        """
        try:
            entry_data = {
                'title': self._extract_title(entry),
                'link': self._extract_link(entry),
                'description': self._extract_description(entry),
                'content': self._extract_content(entry),
                'author': self._extract_author(entry),
                'published': self._extract_published(entry),
                'feed_url': feed_url
            }

            return entry_data

        except Exception as e:
            logger.error(f"Error parsing entry: {e}")
            return None

    def _extract_title(self, entry):
        """Extract entry title."""
        if hasattr(entry, 'title'):
            return html.unescape(entry.title)
        return "Untitled"

    def _extract_link(self, entry):
        """Extract entry link."""
        if hasattr(entry, 'link'):
            return entry.link
        return ""

    def _extract_description(self, entry):
        """Extract entry description."""
        if hasattr(entry, 'description'):
            return html.unescape(entry.description)
        elif hasattr(entry, 'summary'):
            return html.unescape(entry.summary)
        return ""

    def _extract_content(self, entry):
        """Extract full content (content:encoded or similar)."""
        # Try content:encoded first (common in WordPress)
        if hasattr(entry, 'content'):
            if isinstance(entry.content, list) and len(entry.content) > 0:
                return html.unescape(entry.content[0].get('value', ''))

        # Fallback to summary/description
        if hasattr(entry, 'summary_detail'):
            return html.unescape(entry.summary_detail.get('value', ''))

        # Last resort: use description
        return self._extract_description(entry)

    def _extract_author(self, entry):
        """Extract entry author."""
        if hasattr(entry, 'author'):
            return entry.author
        elif hasattr(entry, 'author_detail'):
            return entry.author_detail.get('name', '')
        return None

    def _extract_published(self, entry):
        """Extract published date."""
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            try:
                return datetime(*entry.published_parsed[:6])
            except Exception:
                pass

        if hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            try:
                return datetime(*entry.updated_parsed[:6])
            except Exception:
                pass

        return datetime.now()

    def get_latest_entry(self, feed_url, session=None):
        """
        Get only the latest entry from a feed.

        Args:
            feed_url: URL of RSS feed
            session: requests.Session object

        Returns:
            dict with latest entry data, or None
        """
        feed_data = self.parse_feed(feed_url, session=session)

        if feed_data and feed_data['entries']:
            return feed_data['entries'][0]

        return None
