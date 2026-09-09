"""
Factory for creating AI client and text processor instances.

Uses ModuLLe (vendored in lib/modulle/) for generic AI provider abstraction,
then wraps the results in domain-specific processors for DailyFeedSanity.
"""

from typing import Tuple, Optional
from ..utils.logging_config import get_logger
from .domain_text_processor import DomainTextProcessor
from .domain_vision_processor import DomainVisionProcessor

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


def _resolve_provider_config(user_config):
    """
    Resolve provider configuration from user config and defaults.

    Returns:
        dict with keys: provider, text_model, vision_model, base_url, api_key
    """
    from .. import config as app_config

    # Determine provider
    if user_config and "ai_provider" in user_config:
        provider = user_config["ai_provider"].lower()
    else:
        provider = app_config.AI_PROVIDER.lower()

    logger.info(f"Resolved AI provider: {provider}")

    # Provider-specific config resolution
    provider_defaults = {
        "ollama": {
            "text_model": app_config.TEXT_MODEL,
            "vision_model": app_config.VISION_MODEL,
            "base_url": app_config.OLLAMA_BASE_URL,
            "api_key": None,
        },
        "lm_studio": {
            "text_model": app_config.LM_STUDIO_TEXT_MODEL,
            "vision_model": app_config.LM_STUDIO_VISION_MODEL,
            "base_url": app_config.LM_STUDIO_BASE_URL,
            "api_key": None,
        },
        "lmstudio": {  # alias
            "text_model": app_config.LM_STUDIO_TEXT_MODEL,
            "vision_model": app_config.LM_STUDIO_VISION_MODEL,
            "base_url": app_config.LM_STUDIO_BASE_URL,
            "api_key": None,
        },
        "openai": {
            "text_model": app_config.OPENAI_TEXT_MODEL,
            "vision_model": app_config.OPENAI_VISION_MODEL,
            "base_url": None,
            "api_key": app_config.OPENAI_API_KEY,
        },
        "gemini": {
            "text_model": app_config.GEMINI_TEXT_MODEL,
            "vision_model": app_config.GEMINI_VISION_MODEL,
            "base_url": None,
            "api_key": app_config.GEMINI_API_KEY,
        },
        "claude": {
            "text_model": app_config.CLAUDE_TEXT_MODEL,
            "vision_model": app_config.CLAUDE_VISION_MODEL,
            "base_url": None,
            "api_key": app_config.ANTHROPIC_API_KEY,
        },
        "anthropic": {  # alias
            "text_model": app_config.CLAUDE_TEXT_MODEL,
            "vision_model": app_config.CLAUDE_VISION_MODEL,
            "base_url": None,
            "api_key": app_config.ANTHROPIC_API_KEY,
        },
    }

    defaults = provider_defaults.get(provider, {})

    # User config overrides
    resolved = {
        "provider": provider,
        "text_model": defaults.get("text_model", ""),
        "vision_model": defaults.get("vision_model"),
        "base_url": defaults.get("base_url"),
        "api_key": defaults.get("api_key"),
    }

    if user_config:
        resolved["text_model"] = user_config.get("text_model", resolved["text_model"])
        resolved["vision_model"] = user_config.get(
            "vision_model", resolved["vision_model"]
        )

        # Provider-specific URL/key overrides
        if provider in ("ollama",):
            resolved["base_url"] = user_config.get(
                "ollama_base_url", resolved["base_url"]
            )
        elif provider in ("lm_studio", "lmstudio"):
            resolved["base_url"] = user_config.get(
                "lm_studio_base_url", resolved["base_url"]
            )
        elif provider == "openai":
            resolved["api_key"] = user_config.get("openai_api_key", resolved["api_key"])
        elif provider == "gemini":
            resolved["api_key"] = user_config.get("gemini_api_key", resolved["api_key"])
        elif provider in ("claude", "anthropic"):
            resolved["api_key"] = user_config.get(
                "claude_api_key",
                user_config.get("anthropic_api_key", resolved["api_key"]),
            )

    return resolved


def create_ai_client() -> Tuple[
    object, DomainTextProcessor, Optional[DomainVisionProcessor]
]:
    """
    Create AI client, domain text processor, and domain vision processor.

    Uses ModuLLe for generic provider abstraction, then wraps in domain-specific
    processors that add article summarization, clickbait/ad detection, etc.

    Returns:
        Tuple of (BaseAIClient, DomainTextProcessor, DomainVisionProcessor)
        DomainVisionProcessor may be None if vision model not configured

    Raises:
        ValueError: If configured provider is unknown or API key is missing
        ImportError: If provider module is not available
    """
    from lib.modulle import create_ai_client as modulle_create

    user_config = _load_user_config()
    resolved = _resolve_provider_config(user_config)

    request_timeout = user_config.get("request_timeout") if user_config else None
    if request_timeout:
        try:
            request_timeout = int(request_timeout)
        except (TypeError, ValueError):
            logger.warning(f"Invalid request_timeout in config: {request_timeout!r}, using default")
            request_timeout = None
        if request_timeout is not None and request_timeout <= 0:
            logger.warning(f"request_timeout must be positive: {request_timeout}, using default")
            request_timeout = None

    logger.info(
        f"Creating AI client - Provider: {resolved['provider']}, "
        f"Text: {resolved['text_model']}, Vision: {resolved['vision_model']}"
        + (f", Timeout: {request_timeout}s" if request_timeout else "")
    )

    # Create generic ModuLLe client + processors
    client, text_proc, vision_proc = modulle_create(
        provider=resolved["provider"],
        text_model=resolved["text_model"],
        vision_model=resolved.get("vision_model"),
        base_url=resolved.get("base_url"),
        api_key=resolved.get("api_key"),
        request_timeout=request_timeout,
    )

    # Wrap in domain-specific processors
    domain_text = DomainTextProcessor(
        text_proc, enable_ad_detection=user_config.get("enable_ad_detection", True)
    )
    domain_vision = DomainVisionProcessor(vision_proc) if vision_proc else None

    logger.info(
        f"AI client initialized successfully (provider: {resolved['provider']})"
    )
    return client, domain_text, domain_vision


def create_ai_client_with_fallback() -> Tuple[
    object, DomainTextProcessor, Optional[DomainVisionProcessor]
]:
    """
    Create AI client with fallback to Ollama if configured provider fails.

    Returns:
        Tuple of (BaseAIClient, DomainTextProcessor, DomainVisionProcessor)

    Raises:
        ImportError: If all providers fail to initialize
    """
    try:
        return create_ai_client()
    except (ValueError, ImportError) as e:
        logger.warning(f"Failed to create configured AI client: {e}")

        user_config = _load_user_config()
        from .. import config as app_config

        attempted_provider = (
            user_config.get("ai_provider", app_config.AI_PROVIDER).lower()
            if user_config
            else app_config.AI_PROVIDER.lower()
        )

        if attempted_provider != "ollama":
            logger.info("Falling back to Ollama provider")
            try:
                from lib.modulle import create_ai_client as modulle_create

                request_timeout = (
                    int(user_config["request_timeout"])
                    if user_config and user_config.get("request_timeout")
                    else None
                )

                client, text_proc, vision_proc = modulle_create(
                    provider="ollama",
                    text_model=app_config.TEXT_MODEL,
                    vision_model=app_config.VISION_MODEL,
                    base_url=app_config.OLLAMA_BASE_URL,
                    request_timeout=request_timeout,
                )

                domain_text = DomainTextProcessor(
                    text_proc,
                    enable_ad_detection=user_config.get("enable_ad_detection", True)
                    if user_config
                    else True,
                )
                domain_vision = (
                    DomainVisionProcessor(vision_proc) if vision_proc else None
                )

                logger.info("Ollama fallback client initialized successfully")
                return client, domain_text, domain_vision

            except ImportError as fallback_error:
                logger.error(f"Fallback to Ollama also failed: {fallback_error}")
                raise ImportError("All AI providers failed to initialize")
        else:
            raise
