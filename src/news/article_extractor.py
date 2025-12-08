"""
Article extraction using trafilatura
"""
import trafilatura
from ..utils.logging_config import get_logger
from ..utils.http_client import fetch_url

logger = get_logger(__name__)


class ArticleExtractor:
    """
    Extract article text from web pages using trafilatura.
    """

    def __init__(self):
        """
        Initialize article extractor.
        """
        pass

    def extract_from_url(self, url, session=None):
        """
        Extract article text from URL.

        Args:
            url: Article URL
            session: requests.Session object

        Returns:
            dict with extracted article data, or None on error
        """
        logger.info(f"Extracting article from: {url}")

        try:
            # Fetch page
            response = fetch_url(url, session=session)
            html_content = response.text

            # Extract with trafilatura
            extracted_text = trafilatura.extract(
                html_content,
                include_comments=False,
                include_tables=True,
                no_fallback=False
            )

            if not extracted_text:
                logger.warning(f"Trafilatura could not extract text from {url}")
                return None

            # Extract metadata
            metadata = trafilatura.extract_metadata(html_content)

            result = {
                'url': url,
                'text': extracted_text,
                'title': metadata.title if metadata else None,
                'author': metadata.author if metadata else None,
                'date': metadata.date if metadata else None,
                'description': metadata.description if metadata else None,
            }

            logger.info(f"Extracted {len(extracted_text)} characters from {url}")
            return result

        except Exception as e:
            logger.error(f"Error extracting article from {url}: {e}")
            return None

    def extract_from_feed_entry(self, entry, session=None):
        """
        Extract article from RSS feed entry.

        Args:
            entry: Feed entry dict
            session: HTTP session

        Returns:
            dict with article data
        """
        url = entry.get('link')

        if not url:
            logger.warning("No URL in feed entry")
            return None

        # Try to extract from URL
        article_data = self.extract_from_url(url, session=session)

        if article_data:
            # Merge with feed entry data
            if not article_data['title']:
                article_data['title'] = entry.get('title')

            if not article_data['author']:
                article_data['author'] = entry.get('author')

            if not article_data['description']:
                article_data['description'] = entry.get('description')

            return article_data

        # Fallback: use RSS content
        logger.warning(f"Falling back to RSS content for {url}")

        return {
            'url': url,
            'text': entry.get('content') or entry.get('description', ''),
            'title': entry.get('title'),
            'author': entry.get('author'),
            'date': entry.get('published'),
            'description': entry.get('description'),
            'source': 'rss_fallback'
        }

    def batch_extract(self, entries, session=None):
        """
        Extract multiple articles.

        Args:
            entries: List of feed entry dicts
            session: HTTP session

        Returns:
            List of extracted article dicts
        """
        results = []

        for entry in entries:
            try:
                article = self.extract_from_feed_entry(entry, session=session)
                if article:
                    results.append(article)
            except Exception as e:
                logger.error(f"Error in batch extraction: {e}")

        logger.info(f"Batch extracted {len(results)} articles from {len(entries)} entries")
        return results
