"""
Concurrent feed processing manager for RSS Feed Processor
"""
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from dataclasses import dataclass, field
from typing import List, Dict, Any
from datetime import datetime, timedelta
from .feed_parser import FeedParser
from .feed_classifier import FeedClassifier
from ..utils.logging_config import get_logger
from ..utils.http_client import create_session
from ..config import MAX_CONCURRENT_FEEDS, FEED_TIMEOUT, TIME_FILTER_HOURS

logger = get_logger(__name__)


@dataclass
class ProcessingResults:
    """
    Results from processing all feeds.
    """
    comics: List[Dict[str, Any]] = field(default_factory=list)
    articles: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[Dict[str, str]] = field(default_factory=list)

    def add_comic(self, comic_data):
        """Add comic data to results."""
        self.comics.append(comic_data)

    def add_article(self, article_data):
        """Add article data to results."""
        self.articles.append(article_data)

    def add_error(self, feed_url, error_message):
        """Add error to results."""
        self.errors.append({
            'feed_url': feed_url,
            'error': error_message
        })

    def get_summary(self):
        """Get summary of results."""
        return {
            'comics_count': len(self.comics),
            'articles_count': len(self.articles),
            'errors_count': len(self.errors),
            'total_processed': len(self.comics) + len(self.articles) + len(self.errors)
        }


class FeedManager:
    """
    Manages concurrent processing of multiple RSS feeds.
    """

    def __init__(self, max_workers=MAX_CONCURRENT_FEEDS):
        """
        Initialize feed manager.

        Args:
            max_workers: Maximum number of concurrent workers
        """
        self.max_workers = max_workers
        self.parser = FeedParser()
        self.classifier = FeedClassifier()
        self.all_entries = False  # Will be set during process_all_feeds

    def process_all_feeds(self, feed_urls, all_entries=False):
        """
        Process all feeds concurrently.

        Args:
            feed_urls: List of feed URLs to process
            all_entries: If True, process all news entries; if False, only last 24 hours

        Returns:
            ProcessingResults object
        """
        self.all_entries = all_entries

        if all_entries:
            logger.info(f"Starting concurrent processing of {len(feed_urls)} feeds (ALL entries mode)")
        else:
            logger.info(f"Starting concurrent processing of {len(feed_urls)} feeds (24-hour filter for news)")

        results = ProcessingResults()

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all feeds as tasks
            future_to_url = {
                executor.submit(self._process_single_feed, url): url
                for url in feed_urls
            }

            # Process results as they complete
            for future in as_completed(future_to_url, timeout=FEED_TIMEOUT * len(feed_urls)):
                feed_url = future_to_url[future]

                try:
                    # Get result with timeout
                    result = future.result(timeout=FEED_TIMEOUT)

                    if result:
                        feed_type, data = result

                        if feed_type == 'comic':
                            results.add_comic(data)
                        elif feed_type == 'news':
                            results.add_article(data)

                except TimeoutError:
                    error_msg = f"Processing timed out after {FEED_TIMEOUT}s"
                    logger.error(f"Timeout processing {feed_url}: {error_msg}")
                    results.add_error(feed_url, error_msg)

                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"Error processing {feed_url}: {error_msg}")
                    results.add_error(feed_url, error_msg)

        # Log summary
        summary = results.get_summary()
        logger.info(f"Processing complete: {summary}")

        return results

    def _process_single_feed(self, feed_url):
        """
        Process a single feed.

        Args:
            feed_url: URL of feed to process

        Returns:
            tuple of (feed_type, data) or None on error
        """
        logger.info(f"Processing feed: {feed_url}")

        try:
            # Create session for this feed
            session = create_session()

            # Parse feed
            feed_data = self.parser.parse_feed(feed_url, session=session)

            if not feed_data or not feed_data['entries']:
                logger.warning(f"No entries found in feed: {feed_url}")
                return None

            # Classify feed (pass feed_data for Ollama detection if needed)
            feed_type = self.classifier.classify_feed(feed_url, feed_data=feed_data)
            special_handler = self.classifier.get_special_handler(feed_url)
            feed_name = self.classifier.get_feed_name(feed_url)

            # For comics: use latest entry only
            # For news: use ALL entries
            if feed_type == 'comic':
                # Special cases: Some feeds mix news and comics
                comic_entry = None

                if 'penny-arcade.com' in feed_url:
                    # Penny Arcade: Find first entry with /comic/ in URL
                    for entry in feed_data['entries']:
                        if '/comic/' in entry.get('link', ''):
                            comic_entry = entry
                            break

                elif 'wondermark.com' in feed_url:
                    # Wondermark: Comics have titles starting with #NUMBER
                    for entry in feed_data['entries']:
                        if entry.get('title', '').strip().startswith('#'):
                            comic_entry = entry
                            break

                elif 'buttsmithy.com' in feed_url:
                    # Incase: Comic entries have images in description
                    for entry in feed_data['entries']:
                        desc = entry.get('description', '') or entry.get('summary', '')
                        if '<img' in desc:
                            comic_entry = entry
                            break

                entries_to_process = [comic_entry] if comic_entry else [feed_data['entries'][0]]
            else:  # news
                # Apply 24-hour filter for news feeds unless all_entries flag is set
                if self.all_entries:
                    entries_to_process = feed_data['entries']
                    logger.info(f"Processing ALL {len(entries_to_process)} entries from {feed_name}")
                else:
                    # Filter to entries from last 24 hours
                    cutoff_time = datetime.now() - timedelta(hours=TIME_FILTER_HOURS)
                    entries_to_process = []

                    for entry in feed_data['entries']:
                        # Get published datetime (fallback to current time if not available)
                        published = entry.get('published')

                        # If no published date or entry is within 24 hours, include it
                        if published is None or published >= cutoff_time:
                            entries_to_process.append(entry)

                    logger.info(f"Filtered {len(entries_to_process)}/{len(feed_data['entries'])} entries from last {TIME_FILTER_HOURS} hours for {feed_name}")

            # Build result data
            result_data = {
                'feed_url': feed_url,
                'feed_name': feed_name,
                'feed_type': feed_type,
                'special_handler': special_handler,
                'entries': entries_to_process,
                'session': session  # Pass session for subsequent requests
            }

            logger.info(f"Successfully processed {feed_url} as {feed_type} ({len(entries_to_process)} entries)")
            return (feed_type, result_data)

        except Exception as e:
            logger.error(f"Error in _process_single_feed for {feed_url}: {e}")
            raise  # Re-raise to be caught by executor

    def load_feeds_from_file(self, file_path):
        """
        Load feed URLs from a text file.

        Args:
            file_path: Path to file containing feed URLs (one per line)

        Returns:
            List of feed URLs
        """
        logger.info(f"Loading feeds from {file_path}")

        try:
            with open(file_path, 'r') as f:
                urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]

            logger.info(f"Loaded {len(urls)} feeds from {file_path}")
            return urls

        except Exception as e:
            logger.error(f"Error loading feeds from {file_path}: {e}")
            return []
