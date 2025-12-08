"""
AI Client Abstraction Layer

This module provides an abstraction layer for different AI providers,
allowing the application to switch between Ollama, LM Studio, and other
providers without changing the rest of the codebase.
"""

from .base import BaseAIClient, BaseTextProcessor
from .factory import create_ai_client, create_ai_client_with_fallback

__all__ = [
    'BaseAIClient',
    'BaseTextProcessor',
    'create_ai_client',
    'create_ai_client_with_fallback',
]
