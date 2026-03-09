# AGENTS.md

This file contains guidelines for agentic coding agents operating in this repository.

## Project Overview

RSS Feed Processor - Processes RSS feeds, downloads webcomics, summarizes news articles using AI, and generates HTML digest pages.

## Build/Lint/Test Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run single test
python -m pytest scripts/test_ollama_summarizer.py -v

# Run all tests
python -m pytest scripts/ -v

# Run specific test with args
python scripts/test_ollama_summarizer.py <url> --model "granite4:tiny-h"

# Lint with ruff
ruff check .

# Format with black
black .

# Run main application
python -m src.main

# Run configuration wizard
python -m src.utils.config_wizard
```

## Code Style Guidelines

### General
- Python 3.8+ syntax
- Use type hints for all function parameters and return values
- Follow Google-style docstrings for all public functions and classes

### Naming Conventions
- `snake_case`: functions, variables, modules
- `PascalCase`: classes
- `UPPER_CASE`: constants
- Prefix private methods with underscore

### Imports
- Absolute imports only, no relative imports
- Group imports: standard library → third-party → local modules
- Use explicit imports from modules (avoid `import *`)

### Error Handling
- Use specific exception types (avoid bare `except:`)
- Use `try/except/finally` for cleanup operations
- Log errors with appropriate level using logging module
- Return meaningful error values or raise custom exceptions

### Logging
```python
from .utils.logging_config import get_logger
logger = get_logger(__name__)

logger.debug("Detailed info")
logger.info("General events")
logger.warning("Potential issues")
logger.error("Serious problems")
logger.critical("Severe errors")
```

### Type Hints
```python
from typing import Optional, List, Dict, Any

def process_feed(url: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
    """Process a single feed."""
    pass
```

### Configuration
- All constants in `src/config.py`
- Use environment variables for API keys: `os.getenv('API_KEY', '')`
- Never commit secrets or API keys

### Testing
- Tests in `scripts/` directory
- Use pytest for test execution
- Follow existing patterns in test files
- Test files named `test_*.py` or `*_test.py`

## Project Structure

```
RSS copy (1)/
├── src/                      # Source code
│   ├── main.py               # Main entry point
│   ├── config.py             # Configuration constants
│   ├── ai_client/            # AI provider abstraction
│   │   ├── base.py           # Base abstract classes
│   │   ├── factory.py        # Provider factory
│   │   └── domain_*.py       # Text/Vision processors
│   ├── comics/               # Webcomic downloaders
│   ├── news/                 # Article extraction/summarization
│   ├── feed_processor/       # RSS feed handling
│   ├── output/               # HTML generation
│   └── utils/                # Utilities (logging, file ops)
├── scripts/                  # Test scripts
├── lib/modulle/              # ModuLLe AI abstraction layer
├── output/                   # Generated HTML output
├── temp/                     # Temporary files
└── requirements.txt          # Python dependencies
```

## AI Provider Integration

### Supported Providers
- `ollama` (default) - Local, free
- `lm_studio` - Local, free
- `openai` - Cloud, paid
- `gemini` - Cloud, free tier available
- `claude` - Cloud, paid

### Architecture
- All providers implement `BaseAIClient` interface
- Factory pattern for provider selection
- Health checks required before processing
- Text and vision models configured separately

### Interface Requirements
```python
class BaseAIClient(ABC):
    def health_check(self) -> bool: ...
    def list_models(self) -> List[str]: ...
    def generate(self, model: str, prompt: str, ...) -> Optional[str]: ...
    def chat(self, model: str, messages: List[Dict], ...) -> Optional[str]: ...
```

## Key Components

### Feed Processing
- `FeedManager` - Orchestrates feed processing
- `FeedParser` - Parses RSS/Atom feeds
- `FeedClassifier` - Detects feed type (comic/news)
- Max concurrent feeds: 10
- Per-feed timeout: 120 seconds

### Comics
- `ComicDownloader` - Downloads comic images
- Custom extractors for special comics (Oglaf, Penny Arcade, etc.)
- Vision model for multi-page detection

### News Articles
- `ArticleExtractor` - Extracts article content
- `ContentCleaner` - Cleans HTML/text
- `NewsSummarizer` - Generates AI summaries
- Max article length: 10,000 characters

### Output
- HTML digest page in `output/YYYY-MM-DD/index.html`
- Dark mode support
- Templates in `src/output/templates.py`

## Development Notes

### Concurrency
- Uses `concurrent.futures.ThreadPoolExecutor`
- `MAX_CONCURRENT_FEEDS = 10`
- Use thread-safe operations for shared resources

### HTTP Client
- Custom HTTP client in `src/utils/http_client.py`
- User-Agent rotation
- Retry with exponential backoff
- Timeout: 30 seconds

### Caching
- Feed type cache: `.feed_type_cache.json`
- Language cache: `.feed_language_cache.json`
- Feed overrides via `*_overrides.txt` files

### Command-Line Arguments
- `--debug` - Enable debug logging
- `--ai-provider` - Override AI provider
- `--validate-images` - Enable vision validation
- `--all-entries` - Process all articles (not just 24h)
- `--no-vision` - Disable vision model
- `--feeds` - Custom feed file
- `--output` - Custom output directory

## Dependencies

Core:
- `feedparser` - RSS/Atom parsing
- `requests` - HTTP requests
- `trafilatura` - Web content extraction
- `beautifulsoup4` - HTML parsing
- `Pillow` - Image processing
- `python-dateutil` - Date parsing

## Environment Variables

```bash
OPENAI_API_KEY=
GEMINI_API_KEY=        # or GOOGLE_API_KEY
ANTHROPIC_API_KEY=
```

## For LLM Agents: Current Date

When you need the current date for context (e.g., for time-based filtering, naming, or date-sensitive operations), use:

```bash
date +%Y-%m-%d
```

Or in Python code:
```python
from datetime import datetime
today = datetime.now().strftime('%Y-%m-%d')
```

**Today's date:** Run `date +%Y-%m-%d` to get the current date in the format used by this project (YYYY-MM-DD), which matches the output folder naming convention.
