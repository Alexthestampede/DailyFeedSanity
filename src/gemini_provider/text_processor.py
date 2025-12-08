"""
Text processing with Google Gemini for RSS Feed Processor

This module provides text summarization and title generation using Google's
Gemini API.
"""
from typing import Optional, Dict, Any
from .client import GeminiClient
from ..utils.logging_config import get_logger
from ..config import (
    GEMINI_TEXT_MODEL,
    TEXT_SUMMARY_TEMPERATURE,
    TEXT_TITLE_TEMPERATURE,
    CLICKBAIT_DETECTION_TEMPERATURE,
    LANGUAGE_DETECTION_TEMPERATURE,
    CLICKBAIT_AUTHORS,
    MAX_SUMMARY_LENGTH
)
from ..ai_client.base import BaseTextProcessor

logger = get_logger(__name__)


class GeminiTextClient(BaseTextProcessor):
    """
    Text processor using Google Gemini for summarization and title generation.

    This class implements the same interface as OllamaTextClient, allowing
    for transparent provider switching.
    """

    def __init__(self, api_key: str, model: str = GEMINI_TEXT_MODEL):
        """
        Initialize Gemini text processor.

        Args:
            api_key: Google API key
            model: Gemini model to use
        """
        self.client = GeminiClient(api_key=api_key)
        self.model = model

    def detect_language(self, text: str) -> str:
        """
        Detect the language of the given text.

        Args:
            text: Text to analyze (first 2000 chars used for efficiency)

        Returns:
            Language name (e.g., "English", "Italian", "Spanish") or "English" on error
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for language detection")
            return "English"

        # Use first 2000 chars for efficiency
        excerpt = text[:2000]

        system_prompt = (
            "You are a language detection expert. "
            "Respond with ONLY the language name, nothing else. "
            "Examples: English, Italian, Spanish, French, German, Portuguese, Japanese, Chinese, etc."
        )

        user_prompt = f"What language is this text written in? Respond with only the language name:\n\n{excerpt}"

        try:
            response = self.client.generate(
                prompt=user_prompt,
                system=system_prompt,
                temperature=LANGUAGE_DETECTION_TEMPERATURE,
                model=self.model
            )

            if not response:
                logger.warning("Empty response from language detection, defaulting to English")
                return "English"

            # Clean up response - should be just the language name
            detected_language = response.strip().strip('"\'.,')

            # Validate it's a reasonable response (not too long)
            if len(detected_language) > 50:
                logger.warning(f"Unexpected language detection response: {detected_language[:50]}...")
                return "English"

            logger.debug(f"Detected language: {detected_language}")
            return detected_language

        except Exception as e:
            logger.error(f"Error in language detection: {e}")
            return "English"

    def detect_clickbait(self, title: str, text: str) -> bool:
        """
        Use AI to detect if an article is clickbait.

        Args:
            title: Article title
            text: Article text (first ~1000 chars)

        Returns:
            True if clickbait detected, False otherwise
        """
        try:
            prompt = f"""Analyze this article title and excerpt to determine if it's clickbait.

Title: {title}

Excerpt: {text[:1000]}

Clickbait characteristics include:
- Sensationalized or exaggerated headlines
- Misleading titles that don't match the content
- Emotional manipulation tactics
- "You won't believe..." type language
- Withholding key information to force clicks
- Overly dramatic or provocative language

Respond with ONLY "yes" or "no" - nothing else."""

            system_prompt = "You are an expert at identifying clickbait articles. Respond only with 'yes' or 'no'."

            response = self.client.generate(
                prompt=prompt,
                system=system_prompt,
                temperature=CLICKBAIT_DETECTION_TEMPERATURE,
                model=self.model
            )

            if response:
                answer = response.strip().lower()
                is_clickbait = answer == 'yes'
                if is_clickbait:
                    logger.info(f"Clickbait detected by Gemini for: {title[:50]}...")
                return is_clickbait

            logger.warning("Empty response from clickbait detection")
            return False

        except Exception as e:
            logger.error(f"Error in Gemini clickbait detection: {e}")
            return False

    def generate_summary(self, text: str, title: str = None, author: str = None,
                        max_length: int = MAX_SUMMARY_LENGTH) -> Optional[Dict[str, Any]]:
        """
        Generate a summary of the article text.

        Args:
            text: Article text to summarize
            title: Article title (for clickbait detection)
            author: Article author (for hardcoded clickbait check)
            max_length: Maximum summary length

        Returns:
            Dict with 'summary', 'title', 'is_clickbait', 'clickbait_detected_by' or None on error
        """
        # Check for clickbait via hardcoded author list
        is_clickbait_author = author in CLICKBAIT_AUTHORS if author else False

        # Check for clickbait via AI if we have a title
        is_clickbait_ai = False
        if title:
            is_clickbait_ai = self.detect_clickbait(title, text)

        # Combine detection methods
        is_clickbait = is_clickbait_author or is_clickbait_ai

        # Determine detection method for transparency
        if is_clickbait_author and is_clickbait_ai:
            clickbait_detected_by = "both"
        elif is_clickbait_author:
            clickbait_detected_by = "author"
        elif is_clickbait_ai:
            clickbait_detected_by = "ai"
            logger.info(f"Clickbait detected by Gemini for: {title[:50]}...")
        else:
            clickbait_detected_by = None

        # Step 1: Detect the language of the article
        detected_language = self.detect_language(text)
        logger.info(f"Detected article language: {detected_language}")

        # Step 2: Use appropriate prompt based on detection with explicit language requirement
        if is_clickbait:
            system_prompt = self._get_clickbait_prompt()
            user_prompt = f"IMPORTANT: You MUST respond in {detected_language}. Summarize the following article:\n\n{text[:10000]}"
        else:
            system_prompt = self._get_standard_prompt()
            user_prompt = f"IMPORTANT: You MUST respond in {detected_language}. Summarize the following article:\n\n{text[:10000]}"

        try:
            summary = self.client.generate(
                prompt=user_prompt,
                system=system_prompt,
                temperature=TEXT_SUMMARY_TEMPERATURE,
                model=self.model
            )

            if not summary:
                logger.error("Failed to generate summary")
                return None

            # Truncate if too long
            if len(summary) > max_length:
                summary = summary[:max_length].rsplit('.', 1)[0] + '.'

            # Generate title from summary
            generated_title = self.generate_title(summary)

            return {
                'summary': summary,
                'title': generated_title,
                'is_clickbait': is_clickbait,
                'clickbait_detected_by': clickbait_detected_by
            }

        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return None

    def generate_title(self, summary: str) -> str:
        """
        Generate a concise title from the summary.

        Args:
            summary: Article summary

        Returns:
            Generated title (max 80 chars)
        """
        # Step 1: Detect the language of the summary
        detected_language = self.detect_language(summary)
        logger.debug(f"Detected summary language for title generation: {detected_language}")

        system_prompt = (
            "You are a headline writer. Generate concise, informative titles "
            "that are NOT clickbait. Be straightforward and factual."
        )

        # Step 2: Generate title with explicit language requirement
        user_prompt = f"IMPORTANT: You MUST respond in {detected_language}. Generate a headline for this summary:\n\n{summary}"

        try:
            title = self.client.generate(
                prompt=user_prompt,
                system=system_prompt,
                temperature=TEXT_TITLE_TEMPERATURE,
                model=self.model
            )

            if not title:
                return "Article Summary"

            # Clean up title
            title = title.strip().strip('"\'')

            # Truncate if too long
            if len(title) > 80:
                title = title[:77] + "..."

            return title

        except Exception as e:
            logger.error(f"Error generating title: {e}")
            return "Article Summary"

    def _get_standard_prompt(self) -> str:
        """
        Get standard summarization system prompt.

        Returns:
            System prompt string
        """
        return (
            "You are a helpful assistant that summarizes news articles concisely and accurately. "
            "Focus on the key facts and main points. Keep summaries clear and informative."
        )

    def _get_clickbait_prompt(self) -> str:
        """
        Get clickbait-specific summarization system prompt.

        Returns:
            System prompt string
        """
        return (
            "This article shows signs of clickbait or sensationalism. "
            "Provide an objective, factual summary that strips away dramatic language "
            "and focuses on verifiable facts only. "
            "If no substantial facts exist, state 'Clickbait article with no substantial content.' "
            "Maintain a neutral, skeptical tone and avoid amplifying sensationalism."
        )

    def summarize_article(self, article_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Summarize an article from structured data.

        Args:
            article_data: dict with 'text', 'title', 'author', 'url' fields

        Returns:
            dict with summary results, or None on error
        """
        text = article_data.get('text', '')
        author = article_data.get('author')
        title = article_data.get('title', '')

        if not text:
            logger.error("No text provided for summarization")
            return None

        return self.generate_summary(text, title=title, author=author)
