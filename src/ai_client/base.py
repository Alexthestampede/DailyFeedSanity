"""
Base abstract classes for AI client abstraction layer.

This module provides the abstract base classes that all AI provider clients
must implement to ensure consistent interfaces across different providers
(Ollama, LM Studio, etc.).
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any


class BaseAIClient(ABC):
    """
    Abstract base class for AI provider clients.

    All AI clients (Ollama, LM Studio, etc.) must implement this interface
    to ensure consistent API across different providers.
    """

    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if the AI server is available and responsive.

        Returns:
            True if server is available, False otherwise
        """
        pass

    @abstractmethod
    def list_models(self) -> List[str]:
        """
        List available models on the AI server.

        Returns:
            List of model names, or empty list on error
        """
        pass

    @abstractmethod
    def generate(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.3,
        images: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Generate text using the AI model.

        Args:
            model: Model name to use
            prompt: User prompt
            system: System prompt (optional)
            temperature: Generation temperature (0.0 to 1.0)
            images: List of base64-encoded images for vision models (optional)

        Returns:
            Generated text, or None on error
        """
        pass

    @abstractmethod
    def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.3
    ) -> Optional[str]:
        """
        Chat using the AI model's chat API.

        Args:
            model: Model name to use
            messages: List of message dicts with 'role' and 'content' keys
            temperature: Generation temperature (0.0 to 1.0)

        Returns:
            Generated response, or None on error
        """
        pass


class BaseTextProcessor(ABC):
    """
    Abstract base class for text processing (summarization, title generation).

    All text processors must implement this interface to ensure consistent
    functionality across different AI providers.
    """

    @abstractmethod
    def detect_clickbait(self, title: str, text: str) -> bool:
        """
        Detect if article is clickbait using AI.

        Args:
            title: Article title
            text: Article text excerpt

        Returns:
            True if clickbait detected, False otherwise
        """
        pass

    @abstractmethod
    def generate_summary(
        self,
        text: str,
        title: Optional[str] = None,
        author: Optional[str] = None,
        max_length: int = 500
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a summary of the article text.

        Args:
            text: Article text to summarize
            title: Article title (for clickbait detection)
            author: Article author (for clickbait detection)
            max_length: Maximum summary length in characters

        Returns:
            Dict with keys:
                - 'summary': str - the generated summary
                - 'title': str - generated title
                - 'is_clickbait': bool - clickbait flag
                - 'clickbait_detected_by': str - detection method
            Returns None on error
        """
        pass

    @abstractmethod
    def generate_title(self, summary: str) -> str:
        """
        Generate a concise title from the summary.

        Args:
            summary: Article summary

        Returns:
            Generated title string
        """
        pass

    @abstractmethod
    def summarize_article(self, article_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Summarize an article from structured data.

        Args:
            article_data: Dict with keys:
                - 'text': str - article text
                - 'title': str - article title
                - 'author': str - article author
                - 'url': str - article URL

        Returns:
            Dict with summary results including all fields from generate_summary
            plus original metadata, or None on error
        """
        pass
