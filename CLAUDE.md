# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RSS feed processor that downloads webcomics and summarizes news articles using AI (Ollama or LM Studio). The system processes feeds concurrently, generates summaries, and creates a browsable HTML page with the daily content.

**Current Status**: Fully functional - 12/12 comics downloading, 34 articles from news feeds being processed.

## Usage

### First-Time Setup (Recommended)

Run the interactive configuration wizard to set up your AI provider and RSS feeds:

```bash
python -m src.utils.config_wizard
```

This wizard will guide you through:
- Selecting an AI provider (Ollama, LM Studio, OpenAI, Gemini, or Claude)
- Configuring models and connection settings
- Adding RSS feeds

**See [CONFIG_WIZARD.md](CONFIG_WIZARD.md) for detailed wizard documentation.**

### Running the Processor

```bash
# Basic run (uses Ollama by default)
python -m src.main

# With debug logging
python -m src.main --debug

# Enable image validation (slower)
python -m src.main --validate-images

# Use LM Studio instead of Ollama
python -m src.main --ai-provider lm_studio

# Combine options
python -m src.main --debug --ai-provider lm_studio

# Test AI summarization on any URL (works with both Ollama and LM Studio)
python scripts/test_ollama_summarizer.py https://example.com/article
python scripts/test_ollama_summarizer.py --ai-provider lm_studio https://example.com/article

# Test automatic feed type detection
python scripts/test_feed_type_detection.py                     # Test known feeds
python scripts/test_feed_type_detection.py https://feed.url    # Test specific feed

# Test configuration wizard functions
python scripts/test_config_wizard.py
```

Output: `output/YYYY-MM-DD/index.html`

## Core Requirements

### Output Structure
- Create a dated folder in the execution directory (YYYY-MM-DD format) for each run
- All downloaded files, temporary files, and outputs go in this dated folder
- Files marked for deletion go to a temp folder inside the project (never permanently delete)

### Feed Processing
- Process RSS feeds from `rss.txt` (the only authoritative source - 14 feeds total)
- Use concurrent/threaded processing (10 workers) so unresponsive sites don't block other feeds
- Download webcomics as images, extract and summarize news articles

### AI Integration

The system supports **five AI providers** for text summarization, title generation, clickbait detection, and vision processing:

1. **Ollama** (local, free) - Default
2. **LM Studio** (local, free)
3. **OpenAI** (cloud, paid) - GPT-4o, GPT-4o-mini
4. **Google Gemini** (cloud, free tier + paid) - Gemini 1.5 Flash/Pro
5. **Anthropic Claude** (cloud, paid) - Claude 3.5 Haiku/Sonnet

**Quick Start**:
- Default (Ollama): `python -m src.main`
- Switch provider: `python -m src.main --ai-provider gemini`
- Config file: Set `AI_PROVIDER = 'gemini'` in `src/config.py`

**For detailed provider comparison, setup instructions, and cost estimates, see [AI_PROVIDERS.md](AI_PROVIDERS.md)**

**Provider Capabilities**:
- All providers support: text summarization, title generation, clickbait detection, multi-language, vision/image analysis, feed type detection
- Local providers (Ollama, LM Studio): Free, private, no internet required (after setup)
- Cloud providers (OpenAI, Gemini, Claude): Require API keys, varying costs
- **Recommended for beginners**: Gemini (free tier, easy setup)

**Use Cases**:
1. **Text summarization**: Generate article summaries and titles from extracted text
2. **Feed type detection**: Automatically classify unknown feeds as comic or news
3. **Vision model**: Optional Oglaf multi-page detection (Ollama only, currently simplified to not require vision)

**Feed Type Detection**:
- Unknown feeds are automatically analyzed by the AI provider to determine if they're comics or news
- Results are cached in `.feed_type_cache.json` to avoid repeated analysis
- **Manual Overrides**: User can manually override any feed type in `feed_type_overrides.txt`
- Priority order (highest to lowest):
  1. **Manual overrides** (`feed_type_overrides.txt`) - User always right!
  2. Explicit `FEED_TYPES` config (hardcoded in code)
  3. Cache (`.feed_type_cache.json`)
  4. AI provider detection (automatic)
  5. Default to 'comic' (fallback)
- Falls back gracefully if AI provider is unavailable

**Clickbait Handling**: Articles by "Francesca Testa" get special prompting for objective summarization.

### HTML Output
- Single-page design with collapsible article summaries using `<details>` tags
- Article titles (AI-generated) that expand to show summary on click
- Summary includes link to original article at the end
- Comics displayed using local images but clicking opens the actual webpage
- Clickbait articles highlighted with yellow border and badge

## Special Case Handling

### Mixed Feeds (News + Comics)
Some RSS feeds mix news posts with comic updates. The system filters to find comic entries:

- **Penny Arcade**: Look for `/comic/` in URL (news posts have `/news/post/`)
- **Wondermark**: Comic titles start with `#NUMBER` pattern (e.g., `#1577`)
- **Incase**: Comic entries have `<img>` tags in RSS description

### Comic Extraction Patterns

All comics now working with specific extractors in `src/comics/extractors.py`:

#### Evil Inc
- **Pattern**: `wp-content/uploads/YYYY/MM/YYYYMMDD_evil.jpg` (composite image)
- **Important**: Comics have 6 individual panels (evil01-06.png) PLUS a composite .jpg file
- **Extract**: The composite .jpg (e.g., 20251127_evil.jpg) contains all panels - **2000x1391**
- **Don't Use**: og:image meta tag (points to middle panel only)

#### Penny Arcade
- **Pattern**: `assets.penny-arcade.com/comics/YYYYMMDD-XXXXXXXX.jpg`
- **Format Changed**: Now single image (no more p1/p2/p3 panels)
- **Mixed Feed**: Filter for entries with `/comic/` in URL

#### Oglaf
- **Pattern**: `media.oglaf.com/comic/NAME.jpg`
- **Skip**: Title cards have `tt` prefix (e.g., ttgoat.jpg)
- **Multi-page**: May have multiple images (goat1.jpg, goat2.jpg, etc.)
- **Age Confirmation**: Handled automatically with allow_redirects

#### Widdershins
- **Pattern**: `widdershinscomic.com/comics/TIMESTAMP-NUMBER.png`
- **Example**: `1764796746-125.png` (timestamp + sequential number)

#### Wondermark
- **Pattern**: `wondermark.com/wp-content/uploads/YYYY/MM/YYYY-MM-DD-####xxxx.png`
- **Example**: `2025-11-10-1577robo.png`
- **Mixed Feed**: Filter for titles starting with `#`

#### Incase (Buttsmithy)
- **Pattern**: `incase.buttsmithy.com/wp-content/uploads/YYYY/MM/FILENAME.jpg`
- **Variable Names**: Filenames vary but are sequential (e.g., OG-10.jpg, OG-11.jpg)
- **Mixed Feed**: Filter for entries with images in RSS description

#### Gunnerkrigg Court
- **Pattern**: Extract from `<img class="comic_image">` on comic page

#### Savestate
- **Pattern**: Standard RSS extraction
- **Special**: Remove `-{width}x{height}` dimension suffixes from URLs

#### Other Comics
- **Questionable Content, XKCD, Irovedout, Totempole666**: Use default extractor
- **Important**: WordPress sites often include thumbnail URLs with `-150x150` suffix
- **Fix**: DefaultExtractor removes dimension patterns: `-\d+x\d+` before extension

### News Articles
- Filter and extract clean text using `trafilatura` library before sending to AI provider
- Handle unresponsive sites gracefully without blocking other feeds
- Articles by Francesca Testa require special clickbait-aware prompting
- Process **ALL** entries from news feeds (not just latest like comics)

## Architecture

### Project Structure
```
src/
├── main.py                    # Entry point with CLI
├── config.py                  # All configuration constants
├── feed_processor/            # Concurrent RSS processing
├── comics/                    # Comic extraction and downloading
├── news/                      # Article extraction and summarization
├── ollama_client/             # AI provider integration (Ollama & LM Studio)
├── output/                    # HTML generation
└── utils/                     # Logging, file management, HTTP client

scripts/
└── test_ollama_summarizer.py # Standalone URL testing tool (works with both providers)
```

### Key Design Patterns

**Concurrent Processing**:
- ThreadPoolExecutor with 10 workers
- Each feed processes independently
- Failures don't block other feeds
- Results collected via futures

**Comic Extractors**:
- Abstract base class: `ComicExtractor`
- Specialized extractors for each comic requiring custom logic
- Factory pattern: `get_extractor()` selects appropriate extractor
- Default extractor handles standard RSS feeds

**Error Resilience**:
- Retry with exponential backoff for HTTP requests
- Timeout per feed (120 seconds)
- Safe deletion to temp folder (never rm)
- Graceful degradation (partial success acceptable)

## Common Development Tasks

### Adding a New Comic Feed

1. Add RSS URL to `rss.txt`
2. **Option A**: Let AI auto-detect (recommended for first test)
   - Run the processor and check the logs to see what the AI classifies it as
   - If correct, you're done! Classification is cached automatically.
3. **Option B**: Manually specify in `feed_type_overrides.txt`:
   - Add line: `https://yourfeed.com/rss = comic`
   - Highest priority, always used
4. **Option C**: Add domain to `FEED_TYPES` in `src/config.py` as 'comic' (for hardcoded config)
5. Test with default extractor first: `python -m src.main`
6. If default fails, create custom extractor:
   - Add to `SPECIAL_HANDLERS` in `src/config.py`
   - Create new extractor class in `src/comics/extractors.py`
   - Add to factory in `get_extractor()`

### Adding a New News Feed

1. Add RSS URL to `rss.txt`
2. **Option A**: Let AI auto-detect (recommended for first test)
   - Run the processor and check the logs to see what the AI classifies it as
   - If correct, you're done! Classification is cached automatically.
3. **Option B**: Manually specify in `feed_type_overrides.txt`:
   - Add line: `https://yourfeed.com/rss = news`
   - Highest priority, always used
4. **Option C**: Add domain to `FEED_TYPES` in `src/config.py` as 'news' (for hardcoded config)
5. System will automatically process ALL entries from news feeds

### Manual Feed Type Override

If the AI provider misclassifies a feed or you want to force a specific type:

1. Copy the example template:
   ```bash
   cp feed_type_overrides.example.txt feed_type_overrides.txt
   ```

2. Edit `feed_type_overrides.txt` and add your overrides:
   ```
   https://example.com/feed = comic
   https://another-site.com/rss = news
   ```

3. Run the processor - overrides take effect immediately

**Important Notes**:
- Feed URLs must match exactly (case-sensitive)
- Overrides have HIGHEST priority (even above hardcoded config)
- File supports comments with `#` and blank lines
- Invalid lines are logged as warnings but don't stop processing
- File is gitignored (user-specific configuration)

### Updating AI Models

Edit constants in `src/config.py`:

**For Ollama**:
```python
OLLAMA_TEXT_MODEL = "G47bLDMC"        # For summarization
OLLAMA_VISION_MODEL = "qwen34bvla"     # For image validation
OLLAMA_BASE_URL = "http://192.168.2.150:11434"
```

**For LM Studio**:
```python
LM_STUDIO_MODEL = "qwen3-vl-4b"        # For summarization
LM_STUDIO_BASE_URL = "http://192.168.2.150:1234"
```

## Troubleshooting

### Comic Not Downloading
1. Check if feed is mixed (news + comics) - add filtering in `feed_manager.py`
2. Check if extractor exists in `extractors.py`
3. Run with `--debug` to see extraction attempts
4. Use vision model during development to verify correct image

### Thumbnails Instead of Full Images
- Check for dimension patterns in URL: `-150x150`, `-300x200`, etc.
- DefaultExtractor removes these, but custom extractors may need updates
- Pattern: `re.sub(r'-\d+x\d+(\.(png|jpg|jpeg|gif))', r'\1', image_url)`

### Only One Article from News Feed
- Ensure feed is classified as 'news' not 'comic'
- Check classification priority: manual overrides > FEED_TYPES > cache > AI detection
- Comics get only latest entry, news feeds get ALL entries
- Use manual override to force: `echo "https://your-feed.com/rss = news" >> feed_type_overrides.txt`

### Feed Misclassified by AI
- Check logs to see what the AI classified the feed as
- Override in `feed_type_overrides.txt`:
  ```
  https://misclassified-feed.com/rss = correct_type
  ```
- Or clear cache and re-detect: `rm .feed_type_cache.json`
- Manual overrides always win (highest priority)

### AI Provider Errors

**Ollama**:
- Verify Ollama is running: `curl http://192.168.2.150:11434/api/tags`
- Check model is available: `ollama list`
- Pull models if needed: `ollama pull G47bLDMC`

**LM Studio**:
- Verify LM Studio server is running: `curl http://192.168.2.150:1234/v1/models`
- Check model is loaded in LM Studio GUI
- Ensure the correct model name is configured in `src/config.py`

**General**:
- Try switching providers with `--ai-provider` flag to test if issue is provider-specific
- Check network connectivity to the AI server
- Review logs with `--debug` flag for detailed error messages
