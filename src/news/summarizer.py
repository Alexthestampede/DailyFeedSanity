"""
News article summarizer using AI (Ollama, LM Studio, etc.)
"""
from .article_extractor import ArticleExtractor
from .content_cleaner import ContentCleaner
from ..ai_client.base import BaseTextProcessor
from ..feed_processor.feed_language_detector import FeedLanguageDetector
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class NewsSummarizer:
    """
    Summarize news articles using AI text processor.
    """

    def __init__(self, text_processor=None, language_detector=None):
        """
        Initialize news summarizer.

        Args:
            text_processor: BaseTextProcessor instance (optional, will create default if not provided)
            language_detector: FeedLanguageDetector instance (optional, will create default if not provided)
        """
        self.extractor = ArticleExtractor()
        self.cleaner = ContentCleaner()

        # Use provided text processor or create default one
        if text_processor is None:
            from ..ai_client import create_ai_client_with_fallback
            logger.info("No text processor provided, creating default AI client")
            _, text_processor, _ = create_ai_client_with_fallback()

        self.text_client = text_processor

        # Use provided language detector or create default one
        if language_detector is None:
            logger.info("No language detector provided, creating default")
            language_detector = FeedLanguageDetector()

        self.language_detector = language_detector

    def process_article(self, feed_data):
        """
        Process a news article: extract, clean, and summarize.

        Args:
            feed_data: Feed data dict with entry, feed_url, and optionally language

        Returns:
            dict with processed article, or None on error
        """
        entry = feed_data.get('entry', {})
        feed_name = feed_data.get('feed_name', 'Unknown')
        feed_url = feed_data.get('feed_url', '')
        session = feed_data.get('session')

        # Get language for this feed (might be pre-detected and passed in, or detect now)
        language = feed_data.get('language')
        if not language:
            # Detect language for this feed (will use cache/overrides if available)
            language = self.language_detector.get_feed_language(
                feed_url,
                feed_data=feed_data.get('feed_data')  # Original parsed feed data if available
            )

        logger.info(f"Processing news article from {feed_name} (language: {language})")

        try:
            # Extract article
            article_data = self.extractor.extract_from_feed_entry(entry, session=session)

            if not article_data:
                logger.warning(f"Failed to extract article from {feed_name}")
                return None

            # Clean content
            cleaned_text = self.cleaner.clean_text(article_data['text'])

            # Validate content
            validation = self.cleaner.validate_article_content(cleaned_text)

            if not validation['valid']:
                logger.warning(f"Article validation failed for {feed_name}: {validation['reason']}")
                return {
                    'success': False,
                    'feed_name': feed_name,
                    'error': validation['reason'],
                    'url': article_data['url']
                }

            # Clean title
            cleaned_title = self.cleaner.clean_title(article_data['title'])

            # Summarize with AI (pass language parameter)
            summary_data = self.text_client.generate_summary(
                text=cleaned_text,
                title=cleaned_title,
                author=article_data.get('author'),
                language=language
            )

            if not summary_data:
                logger.error(f"Failed to generate summary for {feed_name}")
                return {
                    'success': False,
                    'feed_name': feed_name,
                    'error': 'Summarization failed',
                    'url': article_data['url']
                }

            # Build result
            result = {
                'success': True,
                'feed_name': feed_name,
                'original_title': cleaned_title,
                'generated_title': summary_data['title'],
                'summary': summary_data['summary'],
                'url': article_data['url'],
                'author': article_data.get('author'),
                'date': article_data.get('date'),
                'is_clickbait': summary_data.get('is_clickbait', False),
                'clickbait_detected_by': summary_data.get('clickbait_detected_by'),
                'word_count': validation['word_count'],
                'source': article_data.get('source', 'extracted'),
                'language': language  # Store detected language for debugging
            }

            logger.info(f"Successfully processed article from {feed_name}")
            return result

        except Exception as e:
            logger.error(f"Error processing article from {feed_name}: {e}")
            return {
                'success': False,
                'feed_name': feed_name,
                'error': str(e),
                'url': entry.get('link', '')
            }

    def batch_process(self, news_feeds):
        """
        Process multiple news articles.

        Args:
            news_feeds: List of feed data dicts (each with multiple entries)

        Returns:
            List of processed articles
        """
        results = []

        for feed_data in news_feeds:
            # Each feed_data now contains 'entries' (plural) instead of 'entry'
            entries = feed_data.get('entries', [])
            feed_name = feed_data.get('feed_name', 'Unknown')
            feed_url = feed_data.get('feed_url', '')

            # Detect language ONCE per feed (not per article)
            language = self.language_detector.get_feed_language(
                feed_url,
                feed_data=feed_data.get('feed_data')  # Original parsed feed data
            )

            logger.info(f"Processing {len(entries)} articles from {feed_name} (language: {language})")

            # Process each entry from this feed
            for entry in entries:
                # Create a single-entry feed_data for process_article
                single_entry_data = {
                    **feed_data,
                    'entry': entry,  # Pass single entry
                    'language': language  # Pass pre-detected language
                }

                result = self.process_article(single_entry_data)
                if result:
                    results.append(result)

        # Summary
        successful = sum(1 for r in results if r.get('success', False))
        failed = len(results) - successful

        logger.info(f"Batch processing complete: {successful} successful, {failed} failed")

        return results

    def summarize_text(self, text, title=None, author=None, language="English"):
        """
        Summarize raw text (utility method).

        Args:
            text: Text to summarize
            title: Optional article title (for clickbait detection)
            author: Optional author name
            language: Language to use for summary (default: "English")

        Returns:
            dict with summary and title
        """
        # Clean text
        cleaned_text = self.cleaner.clean_text(text)

        # Validate
        validation = self.cleaner.validate_article_content(cleaned_text)

        if not validation['valid']:
            logger.warning(f"Text validation failed: {validation['reason']}")
            return None

        # Summarize
        return self.text_client.generate_summary(cleaned_text, title=title, author=author, language=language)
