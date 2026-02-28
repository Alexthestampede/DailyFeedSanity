"""
AI Client Abstraction Layer

Uses ModuLLe (vendored in lib/modulle/) for generic AI provider support,
wrapped with domain-specific processors for DailyFeedSanity.
"""

from .factory import create_ai_client, create_ai_client_with_fallback
from .domain_text_processor import DomainTextProcessor
from .domain_vision_processor import DomainVisionProcessor

__all__ = [
    'DomainTextProcessor',
    'DomainVisionProcessor',
    'create_ai_client',
    'create_ai_client_with_fallback',
]
