"""
Factory for creating AI client and text processor instances.

This module provides factory functions to create the appropriate AI client
and text processor based on the configured provider (Ollama, LM Studio, etc.).
"""
from typing import Tuple, Optional
from ..utils.logging_config import get_logger
from .base import BaseAIClient, BaseTextProcessor

logger = get_logger(__name__)


def _load_user_config():
    """
    Load user configuration from .config.json if it exists.

    Returns:
        Configuration dictionary or None if file doesn't exist
    """
    try:
        from ..utils.config_wizard import load_config
        config = load_config()
        if config:
            logger.info("Loaded user configuration from .config.json")
        return config
    except Exception as e:
        logger.debug(f"Could not load .config.json: {e}")
        return None


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
    # Load user configuration from .config.json if it exists
    user_config = _load_user_config()

    # Import default config
    from .. import config

    # Determine provider: user config takes precedence, then config.py
    if user_config and 'ai_provider' in user_config:
        provider = user_config['ai_provider'].lower()
        logger.info(f"Using AI provider from .config.json: {provider}")
    else:
        provider = config.AI_PROVIDER.lower()
        logger.info(f"Using AI provider from config.py: {provider}")

    if provider == 'ollama':
        try:
            from ..ollama_client.client import OllamaClient
            from ..ollama_client.text_processor import OllamaTextClient
            from ..ollama_client.vision_processor import OllamaVisionClient

            # Get Ollama configuration from user config or defaults
            ollama_base_url = config.OLLAMA_BASE_URL
            text_model = config.TEXT_MODEL
            vision_model = config.VISION_MODEL

            if user_config:
                ollama_base_url = user_config.get('ollama_base_url', ollama_base_url)
                text_model = user_config.get('text_model', text_model)
                vision_model = user_config.get('vision_model', vision_model)

            logger.info(f"Ollama config - URL: {ollama_base_url}, Text: {text_model}, Vision: {vision_model}")

            client = OllamaClient(base_url=ollama_base_url)
            text_processor = OllamaTextClient(model=text_model, base_url=ollama_base_url)
            vision_processor = OllamaVisionClient(model=vision_model, base_url=ollama_base_url) if vision_model else None

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

            # Get LM Studio configuration from user config or defaults
            lm_studio_base_url = config.LM_STUDIO_BASE_URL
            lm_studio_model = config.LM_STUDIO_TEXT_MODEL

            if user_config:
                lm_studio_base_url = user_config.get('lm_studio_base_url', lm_studio_base_url)
                # LM Studio uses same model for both text and vision
                lm_studio_model = user_config.get('text_model', lm_studio_model)

            logger.info(f"LM Studio config - URL: {lm_studio_base_url}, Model: {lm_studio_model}")

            client = LMStudioClient(base_url=lm_studio_base_url)
            text_processor = LMStudioTextClient(model=lm_studio_model, base_url=lm_studio_base_url)
            vision_processor = LMStudioVisionClient(model=lm_studio_model, base_url=lm_studio_base_url)

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

            # Get OpenAI configuration from user config or defaults
            openai_api_key = config.OPENAI_API_KEY
            openai_text_model = config.OPENAI_TEXT_MODEL
            openai_vision_model = config.OPENAI_VISION_MODEL

            if user_config:
                openai_api_key = user_config.get('openai_api_key', openai_api_key)
                openai_text_model = user_config.get('text_model', openai_text_model)
                openai_vision_model = user_config.get('vision_model', openai_vision_model)

            logger.info(f"OpenAI config - Text: {openai_text_model}, Vision: {openai_vision_model}")

            client = OpenAIClient(api_key=openai_api_key)
            text_processor = OpenAITextProcessor(model=openai_text_model, api_key=openai_api_key)
            vision_processor = OpenAIVisionProcessor(model=openai_vision_model, api_key=openai_api_key)

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

            # Get Gemini configuration from user config or defaults
            gemini_api_key = config.GEMINI_API_KEY
            gemini_text_model = config.GEMINI_TEXT_MODEL
            gemini_vision_model = config.GEMINI_VISION_MODEL

            if user_config:
                gemini_api_key = user_config.get('gemini_api_key', gemini_api_key)
                gemini_text_model = user_config.get('text_model', gemini_text_model)
                gemini_vision_model = user_config.get('vision_model', gemini_vision_model)

            if not gemini_api_key:
                raise ValueError("Gemini API key not found")

            logger.info(f"Gemini config - Text: {gemini_text_model}, Vision: {gemini_vision_model}")

            client = GeminiClient(api_key=gemini_api_key)
            text_processor = GeminiTextClient(api_key=gemini_api_key, model=gemini_text_model)
            vision_processor = GeminiVisionClient(api_key=gemini_api_key, model=gemini_vision_model)

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

            # Get Claude configuration from user config or defaults
            anthropic_api_key = config.ANTHROPIC_API_KEY
            claude_text_model = config.CLAUDE_TEXT_MODEL
            claude_vision_model = config.CLAUDE_VISION_MODEL

            if user_config:
                anthropic_api_key = user_config.get('claude_api_key', user_config.get('anthropic_api_key', anthropic_api_key))
                claude_text_model = user_config.get('text_model', claude_text_model)
                claude_vision_model = user_config.get('vision_model', claude_vision_model)

            if not anthropic_api_key:
                raise ValueError("Anthropic API key not found")

            logger.info(f"Claude config - Text: {claude_text_model}, Vision: {claude_vision_model}")

            client = ClaudeClient(api_key=anthropic_api_key)
            text_processor = ClaudeTextClient(api_key=anthropic_api_key, model=claude_text_model)
            vision_processor = ClaudeVisionClient(api_key=anthropic_api_key, model=claude_vision_model)

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

        # Load user config and check provider
        user_config = _load_user_config()
        from .. import config

        # Determine what provider was attempted
        attempted_provider = user_config.get('ai_provider', config.AI_PROVIDER).lower() if user_config else config.AI_PROVIDER.lower()

        if attempted_provider != 'ollama':
            logger.info("Falling back to Ollama provider")
            try:
                from ..ollama_client.client import OllamaClient
                from ..ollama_client.text_processor import OllamaTextClient
                from ..ollama_client.vision_processor import OllamaVisionClient

                # Get Ollama configuration from defaults (fallback mode)
                ollama_base_url = config.OLLAMA_BASE_URL
                text_model = config.TEXT_MODEL
                vision_model = config.VISION_MODEL

                client = OllamaClient(base_url=ollama_base_url)
                text_processor = OllamaTextClient(model=text_model, base_url=ollama_base_url)
                vision_processor = OllamaVisionClient(model=vision_model, base_url=ollama_base_url) if vision_model else None

                logger.info("Ollama fallback client initialized successfully with vision support")
                return client, text_processor, vision_processor

            except ImportError as fallback_error:
                logger.error(f"Fallback to Ollama also failed: {fallback_error}")
                raise ImportError("All AI providers failed to initialize")
        else:
            # Already tried Ollama and it failed
            raise
