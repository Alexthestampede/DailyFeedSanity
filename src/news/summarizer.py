"""
News article summarizer using AI (Ollama, LM Studio, etc.)
"""
from .article_extractor import ArticleExtractor
from .content_cleaner import ContentCleaner
from ..feed_processor.feed_language_detector import FeedLanguageDetector
from ..utils.logging_config import get_logger
from ..config import DECISION_AD_DROP_THRESHOLD, DECISION_PROBE_BATCH_SIZE

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

    def _prepare_article(self, feed_data):
        """
        Stage 1: extract and clean an article without any AI work.

        Args:
            feed_data: Feed data dict with entry, feed_url, and optionally language

        Returns:
            dict with 'item' (article work item or None) and
            'failed_result' (failure dict or None)
        """
        entry = feed_data.get('entry', {})
        feed_name = feed_data.get('feed_name', 'Unknown')
        session = feed_data.get('session')

        try:
            # Extract article
            article_data = self.extractor.extract_from_feed_entry(entry, session=session)

            if not article_data:
                logger.warning(f"Failed to extract article from {feed_name}")
                return {
                    'item': None,
                    'failed_result': {
                        'success': False,
                        'feed_name': feed_name,
                        'error': 'Extraction failed (no content returned from page)',
                        'url': entry.get('link', ''),
                    },
                }

            # Clean content
            cleaned_text = self.cleaner.clean_text(article_data['text'])

            # Validate content
            validation = self.cleaner.validate_article_content(cleaned_text)

            if not validation['valid']:
                logger.warning(f"Article validation failed for {feed_name}: {validation['reason']}")
                return {
                    'item': None,
                    'failed_result': {
                        'success': False,
                        'feed_name': feed_name,
                        'error': validation['reason'],
                        'url': article_data['url'],
                    },
                }

            # Clean title
            cleaned_title = self.cleaner.clean_title(article_data['title'])

            item = {
                'entry': entry,
                'feed_name': feed_name,
                'feed_url': feed_data.get('feed_url', ''),
                'language': feed_data.get('language') or 'English',
                'article_data': article_data,
                'cleaned_text': cleaned_text,
                'cleaned_title': cleaned_title,
                'validation': validation,
                'probe': None,     # filled by the probe stage
                'dropped': False,  # set by the probe stage
            }
            return {'item': item, 'failed_result': None}

        except Exception as e:
            logger.error(f"Error preparing article from {feed_name}: {e}")
            return {
                'item': None,
                'failed_result': {
                    'success': False,
                    'feed_name': feed_name,
                    'error': str(e),
                    'url': entry.get('link', ''),
                },
            }

    def _probe_batch(self, items, batch_size=None):
        """
        Stage 2: decision-model probes for all items, in concurrent batches.

        Probing everything BEFORE any generative call keeps the decision
        model loaded once and the generative model loaded once, instead of
        ping-ponging between models per article. Failures yield probe=None
        (the item stays in generative-verdict flow). Items whose ad
        probability crosses DECISION_AD_DROP_THRESHOLD are marked dropped.

        Args:
            items: List of article work items (mutated in place)
            batch_size: Concurrent probe workers (default from config)
        """
        enabled = (
            hasattr(self.text_client, "probe_verdicts")
            and bool(getattr(self.text_client, "decision_client", None))
        )
        if not enabled:
            return

        if batch_size is None:
            batch_size = DECISION_PROBE_BATCH_SIZE
        batch_size = max(1, batch_size)

        logger.info(f"Stage 2: probing {len(items)} article(s) with the decision model "
                    f"(batches of {batch_size})")

        def _worker(item):
            return self.text_client.probe_verdicts(item['cleaned_title'], item['cleaned_text'])

        concurrent_count = 0

        def _wrap(item):
            nonlocal concurrent_count
            concurrent_count += 1
            if concurrent_count > _wrap.peak:
                _wrap.peak = concurrent_count
            try:
                return _worker(item)
            finally:
                concurrent_count -= 1

        _wrap.peak = 0

        from concurrent.futures import ThreadPoolExecutor, as_completed

        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            future_to_item = {executor.submit(_wrap, item): item for item in items}

            for future in as_completed(future_to_item):
                item = future_to_item[future]
                try:
                    item['probe'] = future.result()
                except Exception as e:
                    logger.warning(f"Probe failed for {item['feed_name']}: {e} "
                                   "- falling back to generative verdicts")
                    item['probe'] = None

                ad_p = (item['probe'] or {}).get('ad_probability')
                if ad_p is not None:
                    logger.info(f"Decision p(ad)={ad_p:.3f}, "
                                f"p(clickbait)={item['probe'].get('clickbait_probability', 0):.3f} "
                                f"for {item['feed_name']}: {item['cleaned_title'][:50]}...")
                    if ad_p >= DECISION_AD_DROP_THRESHOLD:
                        logger.info(f"Pre-filter: pure ad, skipping summarization "
                                    f"for {item['feed_name']}: {item['cleaned_title'][:50]}...")
                        item['dropped'] = True

        dropped = sum(1 for i in items if i['dropped'])
        logger.info(f"Stage 2 complete: {dropped} dropped pre-filter, "
                    f"{len(items) - dropped} proceed to summarization "
                    f"(peak concurrency {max(_wrap.peak, 1)})")

    def _prefiltered_result(self, item):
        """
        Build the result dict for an article dropped by the pre-filter.

        Args:
            item: Article work item with probe results

        Returns:
            Result dict marked 'prefiltered'
        """
        probe = item.get('probe') or {}
        return {
            'success': True,
            'feed_name': item['feed_name'],
            'original_title': item['cleaned_title'],
            'generated_title': item['cleaned_title'],
            'summary': '',
            'url': item['article_data']['url'],
            'author': item['article_data'].get('author'),
            'date': item['article_data'].get('date'),
            'is_clickbait': False,
            'clickbait_detected_by': None,
            'is_ad': True,
            'ad_probability': probe.get('ad_probability'),
            'clickbait_probability': probe.get('clickbait_probability'),
            'decision_model': getattr(self.text_client, 'decision_model', None),
            'word_count': item['validation']['word_count'],
            'source': item['article_data'].get('source', 'extracted'),
            'language': item['language'],
            'prefiltered': True,
        }

    def _summarize_item(self, item):
        """
        Stage 3: generative processing of one survivor (summarize + verdicts).

        Args:
            item: Article work item with probe results (and dropped=False)

        Returns:
            Result dict with processed article, or failure dict on error
        """
        feed_name = item['feed_name']
        language = item['language']
        cleaned_text = item['cleaned_text']
        cleaned_title = item['cleaned_title']
        article_data = item['article_data']

        try:
            # Try single-call JSON workflow first; fall back to multi-call
            summary_data = None
            if hasattr(self.text_client, "generate_summary_single_call"):
                summary_data = self.text_client.generate_summary_single_call(
                    text=cleaned_text,
                    title=cleaned_title,
                    author=article_data.get('author'),
                    language=language,
                    probe=item.get('probe'),
                )
                if not summary_data:
                    logger.info(
                        f"Single-call workflow failed for {feed_name}, "
                        "falling back to multi-call"
                    )
            if not summary_data:
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
                'is_ad': summary_data.get('is_ad', False),
                'clickbait_probability': summary_data.get('clickbait_probability'),
                'ad_probability': summary_data.get('ad_probability'),
                'word_count': item['validation']['word_count'],
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
                'url': article_data.get('url', ''),
            }

    def process_article(self, feed_data):
        """
        Process a single news article through all stages sequentially.

        Convenience path (extraction, probe, summarization one at a time);
        batch_process() is the staged, batched production path.

        Args:
            feed_data: Feed data dict with entry, feed_url, and optionally language

        Returns:
            dict with processed article, or None on error
        """
        entry = feed_data.get('entry', {})
        feed_name = feed_data.get('feed_name', 'Unknown')

        # Get language for this feed (might be pre-detected and passed in, or detect now)
        feed_url = feed_data.get('feed_url', '')
        language = feed_data.get('language')
        if not language:
            # Detect language for this feed (will use cache/overrides if available)
            language = self.language_detector.get_feed_language(
                feed_url,
                feed_data=feed_data.get('feed_data')  # Original parsed feed data if available
            )
        feed_data = {**feed_data, 'language': language}

        logger.info(f"Processing news article from {feed_name} (language: {language})")

        prepared = self._prepare_article(feed_data)
        if prepared['failed_result'] is not None:
            return prepared['failed_result']
        if prepared['item'] is None:
            return None

        item = prepared['item']
        self._probe_batch([item])
        if item['dropped']:
            return self._prefiltered_result(item)
        return self._summarize_item(item)

    def batch_process(self, news_feeds):
        """
        Process multiple news articles with a staged, batched pipeline.

        Stages per feed:
        1. Extract + clean everything (no AI)
        2. Decision-model probes in concurrent batches - one model-load
           window, pure ads dropped here, zero generative calls so far
        3. Survivors summarized sequentially - the generative model loads
           once instead of ping-ponging against the decision model

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

            # Stage 1: extract + clean (no AI)
            items = []
            for entry in entries:
                single_entry_data = {
                    **feed_data,
                    'entry': entry,     # Pass single entry
                    'language': language,  # Pass pre-detected language
                }
                prepared = self._prepare_article(single_entry_data)
                if prepared['failed_result'] is not None:
                    results.append(prepared['failed_result'])
                elif prepared['item'] is not None:
                    items.append(prepared['item'])

            if not items:
                continue

            # Stage 2: decision probes (batches; drops pure ads here)
            self._probe_batch(items)

            # Stage 3: generative processing of survivors only
            for item in items:
                if item['dropped']:
                    results.append(self._prefiltered_result(item))
                else:
                    results.append(self._summarize_item(item))

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
