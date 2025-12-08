"""
Factory for creating AI client and text processor instances.

This module provides factory functions to create the appropriate AI client
and text processor based on the configured provider (Ollama, LM Studio, etc.).
"""
from typing import Tuple, Optional
from ..utils.logging_config import get_logger
from .base import BaseAIClient, BaseTextProcessor

logger = get_logger(__name__)


def create_ai_client() -> Tuple[BaseAIClient, BaseTextProcessor, Optional[object]]:
    """
    Create AI client, text processor, and vision processor instances based on configured provider.

    Returns:
        Tuple of (BaseAIClient, BaseTextProcessor, VisionProcessor) instances
        VisionProcessor may be None if not available for the provider

    Raises:
        ValueError: If configured provider is unknown
        ImportError: If provider module is not available
    """
    # Import AI_PROVIDER here to get current value (may have been changed at runtime)
    from .. import config
    provider = config.AI_PROVIDER.lower()

    logger.info(f"Creating AI client for provider: {provider}")

    if provider == 'ollama':
        try:
            from ..ollama_client.client import OllamaClient
            from ..ollama_client.text_processor import OllamaTextClient
            from ..ollama_client.vision_processor import OllamaVisionClient

            client = OllamaClient()
            text_processor = OllamaTextClient()
            vision_processor = OllamaVisionClient()

            logger.info("Ollama client initialized successfully with vision support")
            return client, text_processor, vision_processor

        except ImportError as e:
            logger.error(f"Failed to import Ollama client: {e}")
            raise ImportError(f"Ollama client not available: {e}")

    elif provider == 'lm_studio' or provider == 'lmstudio':
        try:
            from ..lm_studio_client.client import LMStudioClient
            from ..lm_studio_client.text_processor import LMStudioTextClient
            from ..lm_studio_client.vision_processor import LMStudioVisionClient

            client = LMStudioClient()
            text_processor = LMStudioTextClient()
            vision_processor = LMStudioVisionClient()

            logger.info("LM Studio client initialized successfully with vision support")
            return client, text_processor, vision_processor

        except ImportError as e:
            logger.error(f"Failed to import LM Studio client: {e}")
            raise ImportError(f"LM Studio client not available: {e}")

    elif provider == 'openai':
        try:
            from ..openai_provider.client import OpenAIClient
            from ..openai_provider.text_processor import OpenAITextProcessor
            from ..openai_provider.vision_processor import OpenAIVisionProcessor
            from ..config import OPENAI_TEXT_MODEL, OPENAI_VISION_MODEL

            client = OpenAIClient()
            text_processor = OpenAITextProcessor(model=OPENAI_TEXT_MODEL)
            vision_processor = OpenAIVisionProcessor(model=OPENAI_VISION_MODEL)

            logger.info("OpenAI client initialized successfully with vision support")
            return client, text_processor, vision_processor

        except ValueError as e:
            # API key not found - provide helpful error message
            logger.error(f"Failed to initialize OpenAI client: {e}")
            error_msg = (
                "OpenAI provider requires API key. Please set OPENAI_API_KEY environment variable. "
                "Get your API key from: https://platform.openai.com/api-keys"
            )
            raise ValueError(error_msg)
        except ImportError as e:
            logger.error(f"Failed to import OpenAI client: {e}")
            raise ImportError(f"OpenAI client not available: {e}")

    elif provider == 'gemini':
        try:
            from ..gemini_provider.client import GeminiClient
            from ..gemini_provider.text_processor import GeminiTextClient
            from ..gemini_provider.vision_processor import GeminiVisionClient
            from ..config import GEMINI_API_KEY, GEMINI_TEXT_MODEL, GEMINI_VISION_MODEL

            if not GEMINI_API_KEY:
                raise ValueError("Gemini API key not found")

            client = GeminiClient(api_key=GEMINI_API_KEY)
            text_processor = GeminiTextClient(api_key=GEMINI_API_KEY, model=GEMINI_TEXT_MODEL)
            vision_processor = GeminiVisionClient(api_key=GEMINI_API_KEY, model=GEMINI_VISION_MODEL)

            logger.info("Gemini client initialized successfully with vision support")
            return client, text_processor, vision_processor

        except ValueError as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            error_msg = (
                "Gemini provider requires API key. Please set GEMINI_API_KEY or GOOGLE_API_KEY environment variable. "
                "Get your API key from: https://aistudio.google.com/app/apikey"
            )
            raise ValueError(error_msg)
        except ImportError as e:
            logger.error(f"Failed to import Gemini client: {e}")
            raise ImportError(f"Gemini client not available: {e}")

    elif provider == 'claude' or provider == 'anthropic':
        try:
            from ..claude_provider.client import ClaudeClient
            from ..claude_provider.text_processor import ClaudeTextClient
            from ..claude_provider.vision_processor import ClaudeVisionClient
            from ..config import ANTHROPIC_API_KEY, CLAUDE_TEXT_MODEL, CLAUDE_VISION_MODEL

            if not ANTHROPIC_API_KEY:
                raise ValueError("Anthropic API key not found")

            client = ClaudeClient(api_key=ANTHROPIC_API_KEY)
            text_processor = ClaudeTextClient(api_key=ANTHROPIC_API_KEY, model=CLAUDE_TEXT_MODEL)
            vision_processor = ClaudeVisionClient(api_key=ANTHROPIC_API_KEY, model=CLAUDE_VISION_MODEL)

            logger.info("Claude client initialized successfully with vision support")
            return client, text_processor, vision_processor

        except ValueError as e:
            logger.error(f"Failed to initialize Claude client: {e}")
            error_msg = (
                "Claude provider requires API key. Please set ANTHROPIC_API_KEY environment variable. "
                "Get your API key from: https://console.anthropic.com/"
            )
            raise ValueError(error_msg)
        except ImportError as e:
            logger.error(f"Failed to import Claude client: {e}")
            raise ImportError(f"Claude client not available: {e}")

    else:
        error_msg = (
            f"Unknown AI provider: {provider}. "
            f"Supported providers: 'ollama', 'lm_studio', 'openai', 'gemini', 'claude'"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)


def create_ai_client_with_fallback() -> Tuple[BaseAIClient, BaseTextProcessor, Optional[object]]:
    """
    Create AI client with fallback to Ollama if configured provider fails.

    This function attempts to create the configured provider, and if that fails,
    falls back to Ollama as the default provider.

    Returns:
        Tuple of (BaseAIClient, BaseTextProcessor, VisionProcessor) instances
        VisionProcessor may be None if not available

    Raises:
        ImportError: If all providers fail to initialize
    """
    try:
        return create_ai_client()
    except (ValueError, ImportError) as e:
        logger.warning(f"Failed to create configured AI client: {e}")

        # Fallback to Ollama
        from .. import config
        if config.AI_PROVIDER.lower() != 'ollama':
            logger.info("Falling back to Ollama provider")
            try:
                from ..ollama_client.client import OllamaClient
                from ..ollama_client.text_processor import OllamaTextClient
                from ..ollama_client.vision_processor import OllamaVisionClient

                client = OllamaClient()
                text_processor = OllamaTextClient()
                vision_processor = OllamaVisionClient()

                logger.info("Ollama fallback client initialized successfully with vision support")
                return client, text_processor, vision_processor

            except ImportError as fallback_error:
                logger.error(f"Fallback to Ollama also failed: {fallback_error}")
                raise ImportError("All AI providers failed to initialize")
        else:
            # Already tried Ollama and it failed
            raise
