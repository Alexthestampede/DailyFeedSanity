# RSS Feed Processor

A concurrent RSS feed processor that downloads webcomics, summarizes news articles using Ollama AI, and generates a daily HTML digest page.

## Features

- **Concurrent Processing**: Processes multiple RSS feeds simultaneously using ThreadPoolExecutor
- **Webcomic Downloads**: Automatically downloads the latest webcomics with special handling for:
  - Penny Arcade (downloads all 3 panels)
  - Oglaf (multi-page detection using vision model OCR)
  - Widdershins, Gunnerkrigg Court, Savestate, Wondermark, and more
- **AI-Powered Summarization**: Uses Ollama to generate concise summaries of news articles
- **Clickbait Detection**: Special handling for clickbait authors (e.g., Francesca Testa)
- **HTML Output**: Generates a beautiful, collapsible HTML digest with embedded CSS
- **Safe File Operations**: Never permanently deletes files - moves them to temp folder instead
- **Error Resilience**: Continues processing even if individual feeds fail

## Requirements

- Python 3.8+
- Ollama server running with the following models:
  - `G47bLDMC` (4.2GB) - for text summarization
  - `qwen34bvla` (3.3GB) - for vision tasks (Oglaf multi-page detection)

## Installation

1. Clone or download this repository
2. Install Python dependencies:

```bash
pip install -r requirements.txt
```

3. Ensure Ollama is running and has the required models installed:

```bash
# Check Ollama status
curl http://192.168.2.150:11434/api/tags

# Pull models if needed
ollama pull G47bLDMC
ollama pull qwen34bvla
```

## Configuration

The main configuration is in `src/config.py`. Key settings:

- **Ollama Server**: Default is `http://192.168.2.150:11434`
- **Models**: G47bLDMC for text, qwen34bvla for vision
- **Feed Types**: Classified by domain (comic vs news)
- **Concurrency**: 10 concurrent feed processors
- **Clickbait Authors**: Currently `['Francesca Testa']`

### Feed List

Edit `rss.txt` to customize your RSS feeds (one URL per line):

```
https://www.questionablecontent.net/QCRSS.xml
https://www.penny-arcade.com/feed
https://xkcd.com/rss.xml
https://www.macitynet.it/feed
```

## Usage

### Basic Usage

Process all feeds and generate HTML digest:

```bash
python -m src.main
```

### Command-Line Options

```bash
# Enable debug logging
python -m src.main --debug

# Validate images with vision model (slower)
python -m src.main --validate-images

# Use custom feed list
python -m src.main --feeds custom_feeds.txt

# Disable vision model for Oglaf (faster but single-page only)
python -m src.main --no-vision

# Custom output directory
python -m src.main --output /path/to/output
```

### Test Script

Test the summarizer on a single URL:

```bash
# Basic test
python scripts/test_ollama_summarizer.py https://example.com/article

# Test with clickbait author
python scripts/test_ollama_summarizer.py https://example.com/article --author "Francesca Testa"

# Verbose output
python scripts/test_ollama_summarizer.py https://example.com/article --verbose
```

## Output Structure

The processor creates dated folders with all content:

```
output/
├── 2025-01-15/
│   ├── index.html                    # Main digest page
│   ├── Questionable Content.jpg      # Downloaded comics
│   ├── Penny Arcade-p1.jpg
│   ├── Penny Arcade-p2.jpg
│   ├── Penny Arcade-p3.jpg
│   └── Oglaf.jpg
└── 2025-01-16/
    └── index.html
```

### HTML Output Features

- **Collapsible Sections**: Comics, Articles, and Errors can be expanded/collapsed
- **Clickbait Highlighting**: Clickbait articles are highlighted in yellow with a badge
- **Image Preview**: Comics are displayed inline with links to originals
- **Summary Statistics**: Shows count of comics, articles, and errors
- **Responsive Design**: Works on mobile and desktop

## Special Comic Handlers

### Penny Arcade
Downloads all three panels (p1, p2, p3) by scraping the comic page and generating panel URLs.

### Oglaf
- Scrapes main page for the comic strip
- Detects multi-page comics using "arc" image
- Uses vision model (qwen34bvla) to OCR page count from arc image
- Downloads all pages in sequence

### Widdershins
Extracts comic page link from RSS, then scrapes for `<img id="cc-comic">`.

### Gunnerkrigg Court
Scrapes comic page for `<img class="comic_image">`.

### Savestate
Uses default extraction but removes dimension suffixes (e.g., `-300x200`) from URLs.

### Wondermark
Looks for `<div class="widget">` pattern in RSS content.

## Clickbait Detection

Articles by authors in the `CLICKBAIT_AUTHORS` list receive a special prompt:

> "This article is by Francesca Testa, known for sensationalism and clickbait. Provide an objective, factual summary that strips away dramatic language and focuses on verifiable facts only. If no substantial facts exist, state 'Clickbait article with no substantial content.'"

Clickbait articles are:
- Marked with a yellow badge in the HTML output
- Highlighted with yellow background
- Processed with skeptical summarization

## Error Handling

- **Network Errors**: Automatic retry with exponential backoff
- **Feed Errors**: Individual feed failures don't stop processing
- **Ollama Errors**: Graceful degradation with error reporting
- **File Errors**: Safe deletion to temp folder (never permanent deletion)

All errors are logged and included in the HTML output for review.

## Logging

Logs are saved to `logs/rss_processor_YYYYMMDD_HHMMSS.log`.

Enable debug logging with `--debug` flag for detailed information.

## Safe Deletion

Files are never permanently deleted. Instead, they're moved to `temp/{timestamp}/` for manual review:

```
temp/
├── 20250115_123456/
│   └── old_file.jpg
└── 20250115_140000/
    └── another_file.jpg
```

Temp folders older than 7 days are automatically cleaned up.

## Troubleshooting

### Ollama Connection Error

```
ERROR: Ollama server is not available
```

**Solution**: Check that Ollama is running:
```bash
curl http://192.168.2.150:11434/api/tags
```

If using a different server, update `OLLAMA_BASE_URL` in `src/config.py`.

### Missing Models

```
WARNING: Model 'G47bLDMC' not found
```

**Solution**: Pull the required models:
```bash
ollama pull G47bLDMC
ollama pull qwen34bvla
```

### No Feeds Found

```
ERROR: No feeds found in rss.txt
```

**Solution**: Check that `rss.txt` exists and contains valid URLs (one per line).

### Comic Not Downloading

Check the logs for specific errors. Some comics may require special handlers - see the "Special Comic Handlers" section.

### Slow Processing

- Disable image validation: Don't use `--validate-images` flag
- Disable Oglaf vision model: Use `--no-vision` flag
- Reduce concurrent workers: Edit `MAX_CONCURRENT_FEEDS` in `src/config.py`

## Architecture

```
src/
├── main.py                    # Entry point, orchestration
├── config.py                  # All configuration constants
├── feed_processor/            # RSS feed processing
│   ├── feed_manager.py        # Concurrent processing with ThreadPoolExecutor
│   ├── feed_parser.py         # RSS parsing with feedparser
│   └── feed_classifier.py     # Comic vs news classification
├── comics/                    # Webcomic extraction
│   ├── base_extractor.py      # Abstract base class
│   ├── extractors.py          # Comic-specific extractors
│   └── downloader.py          # Image downloading
├── news/                      # News article processing
│   ├── article_extractor.py   # Text extraction with trafilatura
│   ├── content_cleaner.py     # HTML cleaning and normalization
│   └── summarizer.py          # Ollama summarization
├── ollama_client/             # Ollama API integration
│   ├── client.py              # Base client
│   ├── text_processor.py      # Text summarization
│   └── vision_processor.py    # Vision tasks (OCR, validation)
├── output/                    # HTML generation
│   ├── templates.py           # HTML/CSS templates
│   └── html_generator.py      # Template rendering
└── utils/                     # Utilities
    ├── logging_config.py      # Logging setup
    ├── file_manager.py        # Safe file operations
    └── http_client.py         # HTTP utilities with retries
```

## Contributing

To add a new comic extractor:

1. Add the domain to `FEED_TYPES` in `src/config.py`
2. Add a handler name to `SPECIAL_HANDLERS` if custom extraction is needed
3. Create a new extractor class in `src/comics/extractors.py` extending `ComicExtractor`
4. Add the extractor to the factory function `get_extractor()`

## License

This project is provided as-is for personal use.

## Credits

- RSS parsing: [feedparser](https://github.com/kurtmckee/feedparser)
- Article extraction: [trafilatura](https://github.com/adbar/trafilatura)
- HTML parsing: [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/)
- AI summarization: [Ollama](https://ollama.ai/)
