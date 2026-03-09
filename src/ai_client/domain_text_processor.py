"""
Domain-specific text processor for DailyFeedSanity.

Wraps ModuLLe's generic BaseTextProcessor with RSS-specific methods:
- Article summarization with clickbait/ad detection
- Title generation
- Clickbait detection
- Ad/sponsored content detection

All methods build domain prompts and delegate to ModuLLe's generate().
"""

from datetime import datetime
from typing import Optional, Dict, Any
from ..utils.logging_config import get_logger
from ..config import (
    TEXT_SUMMARY_TEMPERATURE,
    TEXT_TITLE_TEMPERATURE,
    CLICKBAIT_DETECTION_TEMPERATURE,
    CLICKBAIT_AUTHORS,
    AD_DETECTION_TEMPERATURE,
    ENABLE_AD_DETECTION,
)

logger = get_logger(__name__)


class DomainTextProcessor:
    """
    Domain-specific text processor that wraps ModuLLe's generic text processor.

    Provides article summarization, title generation, clickbait detection,
    and ad detection by crafting domain-specific prompts and calling
    the underlying generic generate() method.
    """

    def __init__(self, text_processor, enable_ad_detection=True):
        """
        Initialize domain text processor.

        Args:
            text_processor: ModuLLe BaseTextProcessor instance (has generate() method)
            enable_ad_detection: Enable ad detection feature (default: True)
        """
        self.processor = text_processor
        self.current_date = datetime.now().strftime("%Y-%m-%d")
        self.enable_ad_detection = enable_ad_detection

    def generate(self, prompt, system_prompt=None, temperature=0.7, max_tokens=None):
        """
        Pass-through to underlying ModuLLe text processor's generate() method.

        This allows components like feed detectors to call generate() directly
        for non-domain-specific prompts.

        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            temperature: Sampling temperature
            max_tokens: Maximum tokens (optional)

        Returns:
            Generated text string, or None on error
        """
        return self.processor.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def detect_clickbait(self, title, text):
        """
        Detect if article is clickbait using AI.

        Args:
            title: Article title
            text: Article text (first 1000 chars used)

        Returns:
            bool: True if clickbait detected, False otherwise
        """
        if not title or not text:
            return False

        excerpt = text[:1000]

        system_prompt = (
            "You are a clickbait detection expert. "
            "Analyze the article title and excerpt to determine if it is clickbait. "
            "Clickbait indicators include: "
            "- Sensationalized or exaggerated headlines "
            "- Misleading titles that don't match the content "
            "- Emotional manipulation tactics "
            "- Exaggerated claims or promises "
            "- 'You won't believe...', 'This one trick...', 'Shocking...' type language "
            "- Withholding key information to force clicks "
            "- Overly dramatic or provocative language "
            "Respond with ONLY 'yes' if it is clickbait, or 'no' if it is not."
        )

        user_prompt = f"Title: {title}\n\nExcerpt: {excerpt}\n\nIs this clickbait?"

        try:
            response = self.processor.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=CLICKBAIT_DETECTION_TEMPERATURE,
            )

            if not response:
                logger.warning("Empty response from clickbait detection")
                return False

            response_lower = response.strip().lower()
            if "yes" in response_lower:
                logger.info(f"AI detected clickbait: {title[:50]}...")
                return True
            return False

        except Exception as e:
            logger.error(f"Error in clickbait detection: {e}")
            return False

    def detect_ad(self, title, text):
        """
        Detect if article is an advertisement or sponsored content.

        Args:
            title: Article title
            text: Article text (first 1000 chars used)

        Returns:
            bool: True if ad/sponsored content detected, False otherwise
        """
        if not title or not text:
            return False

        excerpt = text[:1000]

        system_prompt = (
            "You are an advertisement/sponsored content detection expert. "
            "Analyze the article title and excerpt to determine if it is an ad or sponsored content. "
            "Ad/sponsored indicators include: "
            "- Promotional language for a specific product or service "
            "- 'Sponsored', 'Partner', 'Promoted', 'Ad' labels "
            "- Affiliate links or discount codes "
            "- Overly positive product reviews without criticism "
            "- Press releases disguised as articles "
            "- Content that reads like marketing copy "
            "- 'Brought to you by...', 'In partnership with...' language "
            "Respond with ONLY 'yes' if it is an ad/sponsored, or 'no' if it is not."
        )

        user_prompt = f"Title: {title}\n\nExcerpt: {excerpt}\n\nIs this an advertisement or sponsored content?"

        try:
            response = self.processor.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=AD_DETECTION_TEMPERATURE,
            )

            if not response:
                logger.warning("Empty response from ad detection")
                return False

            response_lower = response.strip().lower()
            if "yes" in response_lower:
                logger.info(f"AI detected ad/sponsored content: {title[:50]}...")
                return True
            return False

        except Exception as e:
            logger.error(f"Error in ad detection: {e}")
            return False

    def generate_summary(
        self, text, title=None, author=None, language="English", max_length=500
    ):
        """
        Generate a summary of the article text.

        Args:
            text: Article text to summarize
            title: Article title (for clickbait detection)
            author: Article author (for clickbait detection)
            language: Language to use for the summary
            max_length: Maximum summary length in characters

        Returns:
            dict with 'summary', 'title', 'is_clickbait', 'clickbait_detected_by', 'is_ad',
            or None on error
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for summarization")
            return None

        # Clickbait detection
        is_clickbait_author = author in CLICKBAIT_AUTHORS if author else False
        is_clickbait_ai = False
        if title:
            try:
                is_clickbait_ai = self.detect_clickbait(title, text)
            except Exception as e:
                logger.warning(f"AI clickbait detection failed: {e}")

        is_clickbait = is_clickbait_author or is_clickbait_ai

        if is_clickbait_author and is_clickbait_ai:
            clickbait_detected_by = "both"
        elif is_clickbait_author:
            clickbait_detected_by = "author"
        elif is_clickbait_ai:
            clickbait_detected_by = "ai"
        else:
            clickbait_detected_by = None

        # Ad detection
        is_ad = False
        if title and self.enable_ad_detection:
            try:
                logger.info(
                    f"Running ad detection (enabled={self.enable_ad_detection})"
                )
                is_ad = self.detect_ad(title, text)
            except Exception as e:
                logger.warning(f"AI ad detection failed: {e}")
        elif title:
            logger.info(f"Skipping ad detection (enabled={self.enable_ad_detection})")

        logger.info(f"Generating summary in {language}")

        # Choose prompt based on clickbait status
        if is_clickbait:
            system_prompt = self._get_clickbait_prompt()
        else:
            system_prompt = self._get_standard_prompt()

        user_prompt = f"IMPORTANT: You MUST respond in {language}. Summarize the following article:\n\n{text[:10000]}"

        try:
            summary = self.processor.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=TEXT_SUMMARY_TEMPERATURE,
            )

            if not summary:
                logger.error("Failed to generate summary")
                return None

            # Truncate if too long
            if len(summary) > max_length:
                summary = summary[:max_length].rsplit(".", 1)[0] + "."

            # Generate title from summary
            generated_title = self.generate_title(summary, language=language)

            return {
                "summary": summary,
                "title": generated_title,
                "is_clickbait": is_clickbait,
                "clickbait_detected_by": clickbait_detected_by,
                "is_ad": is_ad,
            }

        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return None

    def generate_title(self, summary, language="English"):
        """
        Generate a concise title from the summary.

        Args:
            summary: Article summary
            language: Language to use for the title

        Returns:
            Generated title string
        """
        logger.debug(f"Generating title in {language}")

        system_prompt = (
            "You are a professional headline writer. "
            "Generate a clear, concise, and informative headline (max 80 characters) "
            "based on the provided summary. "
            "Do not use clickbait language or sensationalism."
        )

        user_prompt = f"IMPORTANT: You MUST respond in {language}. Generate a headline for this summary:\n\n{summary}"

        try:
            title = self.processor.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=TEXT_TITLE_TEMPERATURE,
            )

            if not title:
                return "Article Summary"

            title = title.strip().strip("\"'")
            if len(title) > 80:
                title = title[:77] + "..."

            return title

        except Exception as e:
            logger.error(f"Error generating title: {e}")
            return "Article Summary"

    def summarize_article(self, article_data):
        """
        Summarize an article from structured data.

        Args:
            article_data: dict with 'text', 'title', 'author', 'url' fields

        Returns:
            dict with summary results, or None on error
        """
        text = article_data.get("text", "")
        author = article_data.get("author")
        original_title = article_data.get("title", "")
        url = article_data.get("url", "")

        logger.info(f"Summarizing article: {original_title[:50]}...")

        result = self.generate_summary(text, title=original_title, author=author)

        if result:
            result["original_title"] = original_title
            result["url"] = url
            result["author"] = author

        return result

    def _get_standard_prompt(self):
        """Get standard summarization system prompt."""
        return (
            f"Today is {self.current_date}. "
            "You are a professional news summarizer. "
            "Provide clear, concise, and objective summaries of articles. "
            "Focus on the key facts, main points, and important details. "
            "Maintain a neutral, professional tone. "
            "Keep summaries between 100-300 words."
        )

    def _get_clickbait_prompt(self):
        """Get clickbait-specific summarization system prompt."""
        return (
            f"Today is {self.current_date}. "
            "This article shows signs of clickbait or sensationalism. "
            "Provide an objective, factual summary that strips away dramatic language "
            "and focuses on verifiable facts only. "
            "If no substantial facts exist, state 'Clickbait article with no substantial content.' "
            "Maintain a neutral, skeptical tone and avoid amplifying sensationalism."
        )
