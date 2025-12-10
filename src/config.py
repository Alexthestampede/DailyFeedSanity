"""
Configuration constants for RSS Feed Processor
"""
import os

# AI Provider Configuration
# Supported providers: 'ollama', 'lm_studio', 'openai', 'gemini', 'claude'
AI_PROVIDER = 'ollama'  # Default to Ollama for backward compatibility

# Ollama Configuration
OLLAMA_BASE_URL = "http://localhost:11434"
TEXT_MODEL = "granite4:tiny-h"  # Small, fast model for text summarization
VISION_MODEL = "qwen3-vl:4b"  # Vision-capable model for image OCR/validation

# LM Studio Configuration
LM_STUDIO_BASE_URL = "http://localhost:1234"
LM_STUDIO_TEXT_MODEL = "qwen/qwen3-vl-4b"  # Model for text summarization (use full identifier from /v1/models)
LM_STUDIO_VISION_MODEL = "qwen/qwen3-vl-4b"  # Model for vision processing (must support image inputs)
# Note: LM Studio uses OpenAI-compatible API format
# Note: Vision support requires a vision-capable model loaded in LM Studio

# OpenAI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')  # API key from environment variable
OPENAI_TEXT_MODEL = "gpt-4o-mini"  # Cost-effective model for text summarization
OPENAI_VISION_MODEL = "gpt-4o"  # Model with vision capabilities
# Note: Get your API key from https://platform.openai.com/api-keys
# Cost info (as of 2024):
#   - gpt-4o-mini: $0.150/1M input tokens, $0.600/1M output tokens
#   - gpt-4o: $2.50/1M input tokens, $10.00/1M output tokens (includes vision)

# Google Gemini Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', os.getenv('GOOGLE_API_KEY', ''))  # API key from environment variable
GEMINI_TEXT_MODEL = "gemini-1.5-flash"  # Fast and cost-effective
GEMINI_VISION_MODEL = "gemini-1.5-flash"  # Same model has vision capabilities
# Note: Get API key from https://aistudio.google.com/app/apikey
# Cost info: Gemini 1.5 Flash has generous free tier, very low cost for paid usage

# Anthropic Claude Configuration
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')  # API key from environment variable
CLAUDE_TEXT_MODEL = "claude-3-5-haiku-20241022"  # Fast and cost-effective
CLAUDE_VISION_MODEL = "claude-3-5-haiku-20241022"  # Same model has vision capabilities
# Note: Get API key from https://console.anthropic.com/
# Cost info (as of 2024):
#   - Claude 3.5 Haiku: $0.80/1M input, $4.00/1M output (includes vision)
#   - Claude 3.5 Sonnet: $3.00/1M input, $15.00/1M output (best quality)

# Model Parameters
TEXT_SUMMARY_TEMPERATURE = 0.3
TEXT_TITLE_TEMPERATURE = 0.2
VISION_TEMPERATURE = 0.1
FEED_TYPE_DETECTION_TEMPERATURE = 0.1  # Low temperature for consistent feed classification
CLICKBAIT_DETECTION_TEMPERATURE = 0.1  # Low temperature for consistent clickbait detection
LANGUAGE_DETECTION_TEMPERATURE = 0.1  # Low temperature for consistent language detection (per-article, deprecated)
FEED_LANGUAGE_DETECTION_TEMPERATURE = 0.1  # Low temperature for consistent feed language detection

# Feed Classification
# Comics are processed by downloading images
# News are processed by extracting and summarizing text
FEED_TYPES = {
    # Comics
    'questionablecontent.net': 'comic',
    'penny-arcade.com': 'comic',
    'savestatecomic.com': 'comic',
    'wondermark.com': 'comic',
    'xkcd.com': 'comic',
    'widdershinscomic.com': 'comic',
    'gunnerkrigg.com': 'comic',
    'oglaf.com': 'comic',
    'evil-inc.com': 'comic',
    'irovedout.com': 'comic',
    'totempole666.com': 'comic',
    'buttsmithy.com': 'comic',

    # News
    'macitynet.it': 'news',
    'feedburner.com': 'news',
}

# Special Comic Handlers
# These comics require custom extraction logic
SPECIAL_HANDLERS = {
    'penny-arcade.com': 'penny_arcade',
    'widdershinscomic.com': 'widdershins',
    'gunnerkrigg.com': 'gunnerkrigg',
    'oglaf.com': 'oglaf',
    'savestatecomic.com': 'savestate',
    'wondermark.com': 'wondermark',
    'evil-inc.com': 'evil_inc',
    'buttsmithy.com': 'incase',
}

# Clickbait Authors - require special summarization prompts
CLICKBAIT_AUTHORS = ['Francesca Testa']

# HTTP Settings
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
REQUEST_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
RETRY_BACKOFF = 2  # exponential backoff multiplier

# Concurrency Settings
MAX_CONCURRENT_FEEDS = 10
FEED_TIMEOUT = 120  # seconds per feed

# Time Filtering
TIME_FILTER_HOURS = 24  # Filter news articles to last N hours (can be overridden with --all-entries)

# Content Settings
MAX_ARTICLE_LENGTH = 10000  # characters for Ollama input
MAX_SUMMARY_LENGTH = 500  # characters for summary output

# File Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
TEMP_DIR = os.path.join(BASE_DIR, 'temp')
RSS_FILE = os.path.join(BASE_DIR, 'rss.txt')
LOG_DIR = os.path.join(BASE_DIR, 'logs')
FEED_TYPE_CACHE_FILE = os.path.join(BASE_DIR, '.feed_type_cache.json')  # Cache for Ollama feed classification
FEED_TYPE_OVERRIDES_FILE = os.path.join(BASE_DIR, 'feed_type_overrides.txt')  # Manual feed type overrides
FEED_LANGUAGE_CACHE_FILE = os.path.join(BASE_DIR, '.feed_language_cache.json')  # Cache for feed language detection
FEED_LANGUAGE_OVERRIDE_FILE = os.path.join(BASE_DIR, 'feed_language_overrides.txt')  # Manual feed language overrides

# Logging
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Output HTML Settings
HTML_TITLE = "DailyFeedSanity"
DATE_FORMAT = '%Y-%m-%d'
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

# Image Validation (optional feature)
VALIDATE_IMAGES = False  # Can be overridden by command-line flag
MIN_IMAGE_SIZE = 100  # pixels (width or height)
ALLOWED_IMAGE_FORMATS = ['JPEG', 'PNG', 'GIF', 'WEBP']
