# Configuration Wizard Guide

The Configuration Wizard is an interactive tool for setting up and managing your RSS Feed Processor configuration. It provides an easy way to configure AI providers, select models, and manage RSS feeds without manually editing configuration files.

## Quick Start

### First Run Setup

When you run the wizard for the first time, it will guide you through:

```bash
python -m src.utils.config_wizard
```

The wizard will help you:
1. Select an AI provider (Ollama, LM Studio, OpenAI, Gemini, or Claude)
2. Configure connection settings (URLs for local providers, API keys for cloud providers)
3. Select text and vision models
4. Add at least one RSS feed

### Subsequent Runs

After initial setup, the wizard displays an interactive menu for managing your configuration:

```
Options:
  [1] Change AI provider
  [2] Change text model
  [3] Change vision model
  [4] Add RSS feed
  [5] Remove RSS feed
  [6] View all feeds
  [7] Test AI connection
  [8] Reset configuration
  [9] View language overrides        # Shows all manual language settings
 [10] Add language override          # Set feed language (e.g., Italian→English)
 [11] Remove language override       # Delete specific override
 [12] Clear language cache           # Force fresh language detection
 [13] Exit
```

## AI Provider Selection

### Local Providers (Free)

#### Ollama
- **Requirements**: Ollama server running locally or on network
- **Default URL**: `http://localhost:11434`
- **Setup**: Download from https://ollama.com/download
- **Features**:
  - Full model inspection (parameters, context size, vision capabilities)
  - Separate text and vision model selection
  - Context size warnings for models under 4k
  - Vision model optional

**Recommended Models**:
- **Text**: `granite4:tiny-h` - Fast, efficient, good quality summaries
- **Vision**: `qwen3-vl:4b` - Vision-capable, good for image analysis
- **All-in-one**: `qwen3-vl:30b-a3b` - For users with 16GB+ VRAM, handles both text and vision excellently

**Setup Process**:
1. Enter Ollama server URL (or use default)
2. Wizard tests connection and lists available models
3. Select text model from filtered list
4. Optionally select vision model

**Model Display Format**:
```
  [1] model-name
      Parameters: 7.2B, Size: 4.5 GB
      Context: 8192
      Vision: No
```

Models with context < 4096 show a warning during selection.

#### LM Studio
- **Requirements**: LM Studio running with a model loaded
- **Default URL**: `http://localhost:1234`
- **Setup**: Download from https://lmstudio.ai/
- **Features**:
  - Lists loaded models via OpenAI-compatible API
  - Single model for both text and vision tasks
  - Simpler setup than Ollama

**Recommended Models**:
- **All-in-one**: `qwen3-vl:4b` or `qwen3-vl:30b-a3b` - Handles both text and vision

**Setup Process**:
1. Enter LM Studio server URL (or use default)
2. Wizard tests connection and lists loaded models
3. Select model (used for both text and vision)

**Note**: LM Studio uses the same model for all tasks. Ensure your selected model supports vision if you plan to use image validation features.

### Cloud Providers (Paid)

#### OpenAI
- **Cost**: GPT-4o-mini (~$0.15/1M input tokens), GPT-4o (~$2.50/1M input tokens)
- **API Key**: Get from https://platform.openai.com/api-keys
- **Default Models**:
  - Text: `gpt-4o-mini` (cost-effective)
  - Vision: `gpt-4o` (includes vision capabilities)

**Cost Warning**: You will be shown a warning that using OpenAI will incur costs at your risk. You must explicitly accept to continue.

#### Google Gemini
- **Cost**: Generous free tier, low paid costs
- **API Key**: Get from https://aistudio.google.com/app/apikey
- **Default Models**:
  - Text: `gemini-1.5-flash`
  - Vision: `gemini-1.5-flash` (same model)
- **Recommended**: Best option for beginners (free tier)

**Note**: Gemini has a free tier, but exceeding limits may incur costs.

#### Anthropic Claude
- **Cost**: Claude 3.5 Haiku (~$0.80/1M input tokens)
- **API Key**: Get from https://console.anthropic.com/
- **Default Models**:
  - Text: `claude-3-5-haiku-20241022`
  - Vision: `claude-3-5-haiku-20241022` (same model)

**Cost Warning**: You will be shown a warning about token costs at your risk.

## Configuration File

The wizard saves configuration to `.config.json` in the project root:

```json
{
  "ai_provider": "ollama",
  "ollama_base_url": "http://localhost:11434",
  "text_model": "granite4:tiny-h",
  "vision_model": "qwen3-vl:4b",
  "rss_feeds": [
    "https://example.com/feed1",
    "https://example.com/feed2"
  ],
  "first_run_complete": true
}
```

**Note**: `.config.json` is gitignored and user-specific.

## Managing RSS Feeds

### Adding Feeds

The wizard validates URLs and adds them to both:
1. The `.config.json` file (for the wizard)
2. The `rss.txt` file (for the main processor)

This ensures synchronization between both systems.

### Removing Feeds

Removes feeds from both `.config.json` and `rss.txt` to maintain consistency.

### Viewing Feeds

Displays all configured feeds with numbering for easy reference.

## Managing Feed Languages

The RSS processor uses a **feed-level language detection system** that detects the language of each feed ONCE (not per article). This provides massive efficiency gains and solves common multi-language issues.

### How Language Detection Works

**The Problem It Solves**:
- **Scenario**: Italian tech news site (macitynet.it) publishes articles in Italian
- **Without language detection**: AI summarizes each article in Italian (not helpful for English readers)
- **With language detection**: System detects "Italian" for macitynet.it domain, instructs AI to always summarize in English
- **Bonus**: Detects once per feed domain, cached permanently (massive token savings)

**Priority Order** (highest to lowest):
1. **Manual overrides** (`feed_language_overrides.txt`) - User always right!
2. Hardcoded config (`LANGUAGE_OVERRIDES` in `config.py`)
3. Cache (`.feed_language_cache.json`) - Auto-managed
4. AI detection (automatic on first article)
5. Default to None (no override, AI decides)

**Efficiency Benefits**:
- Traditional per-article detection: 100 articles × 500 tokens = 50,000 tokens wasted
- Feed-level detection: 1 feed × 500 tokens = 500 tokens total
- **100x reduction** in language detection costs!

**Cache Behavior**:
- Language detected once per feed domain (e.g., "macitynet.it")
- Stored in `.feed_language_cache.json` (auto-managed, gitignored)
- Persists across runs indefinitely
- Only cleared when you explicitly clear cache or delete file

### Common Use Cases

**Use Case 1: Italian Tech News → English Summaries**
```
Problem: macitynet.it publishes in Italian, summaries come out in Italian
Solution: Add override → macitynet.it = English
Result: All macitynet.it articles always summarized in English
```

**Use Case 2: Chinese Leaker on English Forum**
```
Problem: English forum feed contains Chinese leaker posts, AI summarizes in Chinese
Solution: Add override → forum-domain.com = English
Result: Even Chinese posts get English summaries
```

**Use Case 3: Multi-Language Feed**
```
Problem: Feed mixes English and Spanish articles, inconsistent summaries
Solution: Add override → domain.com = English
Result: All articles from that feed summarized in English
```

**Use Case 4: Force English for Everything**
```
Solution: Add wildcard overrides for all your feeds
Result: Every feed summarized in English regardless of source language
```

## Managing Language Overrides

The wizard provides tools to manage language overrides for feeds. By default, the RSS processor uses AI to detect the language of each feed automatically, but you can override this detection for specific feeds.

### Viewing Language Overrides (Option 9)

Menu option **[9] View language overrides** displays all configured overrides:

```
Language Overrides
==================================================

macitynet.it              → English
feedburner.com/psblog     → English
9to5mac.com               → English
ansa.it                   → English

Total: 4 override(s)
```

**What This Shows**:
- Domain or URL pattern (left side)
- Target language for summaries (right side)
- Total count of active overrides

**Interpretation**:
- `macitynet.it → English` means: "Detect that macitynet.it is Italian, but always summarize in English"
- These overrides apply to ALL articles from these feeds
- Overrides persist across runs (stored in `feed_language_overrides.txt`)

**If No Overrides Configured**:
The wizard shows helpful instructions on how to add overrides using option [10].

**When to Use**:
- Check current language settings before adding new ones
- Verify overrides were added correctly
- Review which feeds have custom language settings
- Quick reference for troubleshooting

### Adding Language Overrides (Option 10)

Menu option **[10] Add language override** guides you through adding a new override:

**Step 1: Enter the domain or URL**

You have three format options:
- **Just domain**: `macitynet.it` (recommended, matches all subdomains)
- **Domain with path**: `feedburner.com/psblog` (specific feed path)
- **Full URL**: `https://www.macitynet.it/feed/` (exact match)

**Which format to use?**
- Use **just domain** for most cases (simplest and broadest)
- Use **domain with path** if you have multiple feeds from same domain with different languages
- Use **full URL** only if you need exact matching

**Step 2: Enter the target language**

The language you want summaries to be in (NOT the source language):

**Common languages**: English, Italian, Spanish, French, German, Chinese, Japanese, Korean, Portuguese, Russian, Arabic, Hindi

**Important**:
- Enter the language you want **summaries in**, not the source language
- For Italian news site → use "English" to get English summaries
- For Chinese forum → use "English" to get English summaries
- Language names are automatically capitalized for consistency

**Interactive Example**:
```
Enter domain or URL: macitynet.it

Common languages: English, Italian, Spanish, French, German, Chinese, Japanese
You can enter any language name.

Enter language: English

Language override added: macitynet.it → English

This means: Articles from macitynet.it (Italian site) will be summarized in English
```

**Features**:
- ✅ Validates input format
- ✅ Checks for existing overrides (prompts to replace)
- ✅ Preserves comments and formatting in file
- ✅ Creates `feed_language_overrides.txt` if missing
- ✅ Auto-capitalizes language names
- ✅ Immediate effect (no restart required)

**Real-World Workflow**:
```
You notice: macitynet.it articles are summarized in Italian
You want: Summaries in English for easier reading
Solution:
  1. Run wizard → [10]
  2. Enter: macitynet.it
  3. Enter: English
  4. Next run: All macitynet.it articles summarized in English
```

### Removing Language Overrides (Option 11)

Menu option **[11] Remove language override** displays a numbered list and lets you select which override to remove:

```
Current language overrides:

  [1] macitynet.it → English
  [2] feedburner.com/psblog → English
  [3] 9to5mac.com → English

Select override to remove [1-3, or 'c' to cancel]: 1

Override removed: macitynet.it → English
```

**What Happens After Removal**:
- Override is deleted from `feed_language_overrides.txt`
- Next system priority is used (cache → AI detection → default)
- If language was cached, cached value will be used
- To force re-detection, clear cache with option [12]

**Features**:
- ✅ Shows all current overrides with numbers
- ✅ Simple selection by number
- ✅ Cancel with 'c' (no changes)
- ✅ Preserves comments and formatting
- ✅ Confirms removal with message
- ✅ Immediate effect

**When to Use**:
- Remove override to let AI detect language automatically
- Clean up old/unused overrides
- Test AI language detection accuracy
- Simplify configuration

### Clearing Language Cache (Option 12)

Menu option **[12] Clear language cache** deletes the `.feed_language_cache.json` file:

```
This will force all feed languages to be re-detected on the next run.

Are you sure? [y/N]: y

Language cache cleared successfully.
Languages will be re-detected on next run.
```

**What This Does**:
- Deletes `.feed_language_cache.json` (auto-managed cache file)
- Forces AI to re-detect language for ALL feeds on next run
- Does NOT affect manual overrides (they always take priority)
- Does NOT delete or modify `feed_language_overrides.txt`

**When to Use**:
1. **AI detection was wrong**: Cache has incorrect language, want fresh detection
2. **After model upgrade**: New AI model might detect languages better
3. **Testing**: Want to see what AI detects without cache
4. **Corrupted cache**: File became invalid or inconsistent
5. **Feed language changed**: Site switched from Italian to English content

**What Happens on Next Run**:
```
Before clearing cache:
  macitynet.it → (cached: Italian) → Summarize in English

After clearing cache:
  macitynet.it → (no cache) → AI detects Italian → Summarize in English
  Result: Same outcome, but fresh detection
```

**Important Notes**:
- ⚠️ Next run will use more tokens (one detection per feed)
- ✅ Manual overrides still work (highest priority)
- ✅ New detections will be cached automatically
- ✅ One-time token cost, then cached again

**Example Workflow**:
```
Situation: AI detected Spanish for a site, but it's actually Portuguese
Solution:
  1. Option [12] → Clear cache
  2. Next run → AI re-detects as Portuguese
  3. If still wrong → Option [10] → Add manual override
```

### Language Override Priority

The system uses this priority order (highest to lowest):

1. **Manual overrides** (`feed_language_overrides.txt`) ← Managed by wizard options 9-12
2. Hardcoded config (`LANGUAGE_OVERRIDES` in `config.py`) ← Developer defaults
3. Cache (`.feed_language_cache.json`) ← Auto-managed, persistent
4. AI detection (automatic) ← Runs once per feed, then cached
5. Default to None (no language override) ← AI decides per article

**Visual Priority Flow**:
```
Feed URL → Check manual overrides → Found? Use it (DONE)
         ↓
         Check hardcoded config → Found? Use it (DONE)
         ↓
         Check cache → Found? Use it (DONE)
         ↓
         Ask AI to detect → Cache result → Use it (DONE)
         ↓
         Default: None (AI decides per article)
```

**Important**:
- Manual overrides (wizard-managed) always win
- Once detected, language is cached indefinitely
- Clearing cache forces re-detection but keeps overrides
- Overrides are per-domain, not per-article

**Token Cost Implications**:
```
No override, no cache:    500 tokens × N articles = High cost
No override, with cache:  500 tokens × 1 feed = One-time cost
With override:            0 tokens (no detection needed)
```

### Example Workflows

**Workflow 1: Fix Italian Site Summaries**
```
Problem: macitynet.it articles appear in Italian
Goal: Get English summaries

Steps:
  1. python -m src.utils.config_wizard
  2. Select [10] Add language override
  3. Enter domain: macitynet.it
  4. Enter language: English
  5. Done! Next run will summarize in English

Result: All macitynet.it articles forever summarized in English
```

**Workflow 2: Review and Clean Up Overrides**
```
Scenario: Not sure what overrides you have

Steps:
  1. python -m src.utils.config_wizard
  2. Select [9] View language overrides
  3. Review list of all overrides
  4. If any are wrong/old: Select [11] Remove language override
  5. Select the number to remove

Result: Clean, accurate override list
```

**Workflow 3: Fresh Start with Language Detection**
```
Scenario: Want AI to re-detect all languages from scratch

Steps:
  1. python -m src.utils.config_wizard
  2. Select [12] Clear language cache
  3. Confirm with 'y'
  4. Run RSS processor: python -m src.main
  5. Check logs for new detections

Result: Fresh AI language detection for all feeds
Note: Will use more tokens on this run (one-time cost)
```

**Workflow 4: Multi-Language Feed Forcing**
```
Scenario: Feed mixes English and Chinese, summaries inconsistent
Goal: Always get English summaries

Steps:
  1. python -m src.utils.config_wizard
  2. Select [10] Add language override
  3. Enter domain: mixed-language-site.com
  4. Enter language: English
  5. Run processor

Result: All articles from that feed summarized in English,
        regardless of source language
```

## Testing AI Connection

The wizard can test your AI provider connection:

**Local Providers (Ollama/LM Studio)**:
- Tests server connectivity
- Lists available models
- Verifies models are loaded

**Cloud Providers**:
- Displays API key status (first 8 characters shown)
- Notes that actual API testing requires making a call (not done automatically)

## Model Selection Features

### Context Size Filtering

- **Minimum Recommended**: 4096 tokens
- Models below 4k show warnings during selection
- User can proceed with low-context models (with confirmation)

### Vision Model Detection

For Ollama:
- Automatically filters for vision-capable models
- Checks for "vl" in family name
- Checks for vision/CLIP/projector parameters
- Can skip vision model selection (optional)

For LM Studio:
- Uses same model for text and vision
- User responsible for ensuring vision support

### Model Information Display

Shows comprehensive details:
- Model name
- Parameter count (e.g., 7.2B, 13B)
- Model size on disk (e.g., 4.5 GB)
- Context window size
- Vision capability (Yes/No)
- Warnings for low context

## Error Handling

The wizard handles errors gracefully:

**Connection Failures**:
- Clear error messages
- Setup instructions (download URLs)
- Option to retry or cancel

**Invalid Input**:
- URL validation for RSS feeds
- Number range validation for menu selections
- Helpful prompts for retry

**File Errors**:
- Handles missing/corrupt config files
- Rolls back changes if file writes fail
- Shows descriptive error messages

## Advanced Usage

### Changing AI Provider

**Warning**: Changing providers requires full reconfiguration because different providers have different settings (URLs vs API keys, different model names, etc.).

The wizard will:
1. Warn about reconfiguration requirement
2. Ask for confirmation
3. Run full provider setup
4. Preserve RSS feeds from old config
5. Save updated configuration

### Reset Configuration

Completely deletes `.config.json` and requires running setup again. Use this to:
- Start fresh with different settings
- Fix corrupted configuration
- Remove sensitive API keys

**Note**: This does NOT delete `rss.txt` - your feeds are preserved.

### Manual Configuration

While the wizard is the recommended way to configure the system, you can also manually edit `.config.json` if needed. The wizard will respect manual changes on next run.

## Integration with Main Processor

The configuration wizard is **optional**. The main RSS processor (`src/main.py`) still uses the traditional configuration methods:

1. `src/config.py` - Default settings and constants
2. Command-line arguments - Override provider, debug mode, etc.
3. Environment variables - API keys for cloud providers

The wizard is provided as a convenience tool for easier setup, especially for first-time users.

## Troubleshooting

### "Failed to connect to Ollama/LM Studio"

**Solutions**:
1. Verify server is running: `curl http://localhost:11434/api/tags` (Ollama)
2. Check URL is correct (IP address, port)
3. Ensure no firewall blocking connections
4. For LM Studio: verify a model is loaded in the GUI

### "No models found on server"

**Ollama**:
```bash
# List models
ollama list

# Pull a model if needed
ollama pull granite4:tiny-h
```

**LM Studio**:
1. Open LM Studio GUI
2. Download a model from the search tab
3. Load the model (server must be running)

### "Invalid URL format"

RSS feed URLs must include:
- Scheme: `http://` or `https://`
- Domain: `example.com`
- Path (optional): `/feed`

Examples:
- Valid: `https://example.com/feed.xml`
- Invalid: `example.com/feed` (missing scheme)

### "Configuration file corrupt"

If `.config.json` gets corrupted:
1. Delete it: `rm .config.json`
2. Run wizard again: `python -m src.utils.config_wizard`
3. Go through first-run setup

## Helper Functions API

The wizard provides two helper functions that can be imported and used by other scripts:

```python
from src.utils.config_wizard import load_config, save_config

# Load configuration
config = load_config()  # Returns dict or None

# Save configuration
success = save_config(config_dict)  # Returns True/False
```

**Use Cases**:
- Scripts that need to read user's AI provider preference
- Tools that validate configuration before running
- Custom configuration management tools

## Best Practices

1. **Run wizard before first use**: Sets up everything properly
2. **Test connection after setup**: Verify AI provider works
3. **Add multiple feeds**: More variety in your digest
4. **Use local providers for privacy**: No data sent to cloud
5. **Keep API keys secure**: Never commit `.config.json` to git
6. **Use vision models sparingly**: Only if you need image validation (slower)

## Example Workflows

### Setup for Beginners (Gemini)

Best for users who want easy setup with minimal configuration:

```bash
python -m src.utils.config_wizard
# Select [4] Google Gemini
# Get free API key from provided URL
# Use default models (gemini-1.5-flash)
# Add RSS feeds
```

### Setup for Privacy (Ollama)

Best for users who want complete privacy and local processing:

```bash
# Install Ollama first
curl -fsSL https://ollama.com/install.sh | sh

# Pull models
ollama pull granite4:tiny-h       # Text model
ollama pull qwen3-vl:4b           # Vision model (optional)

# OR pull the all-in-one model (requires 16GB+ VRAM)
ollama pull qwen3-vl:30b-a3b      # Both text and vision

# Run wizard
python -m src.utils.config_wizard
# Select [1] Ollama
# Use default URL (http://localhost:11434)
# Select granite4:tiny-h for text (or qwen3-vl:30b-a3b for everything)
# Select qwen3-vl:4b for vision (or skip if using 30b model)
# Add RSS feeds
```

### Setup for Advanced Users (LM Studio)

Best for users who want GUI model management:

```bash
# Install LM Studio from https://lmstudio.ai/
# Download and load a model in the GUI
# Start the server (Server tab in LM Studio)

# Run wizard
python -m src.utils.config_wizard
# Select [2] LM Studio
# Use default URL (http://localhost:1234)
# Select loaded model
# Add RSS feeds
```

## FAQ

**Q: Do I need to use the wizard?**
A: No, it's optional. You can still configure via `src/config.py` and command-line arguments.

**Q: Can I switch between providers easily?**
A: Yes, use menu option [1] to change providers. Your RSS feeds are preserved.

**Q: What happens to my API keys?**
A: They're stored in `.config.json` which is gitignored for security.

**Q: Can I use multiple AI providers?**
A: Not simultaneously, but you can switch between them using the wizard.

**Q: Does the wizard modify rss.txt?**
A: Yes, when adding/removing feeds to keep both files synchronized.

**Q: What if I don't want a vision model?**
A: Vision models are optional. Skip the selection during setup (Ollama only).

**Q: How do I update models without reconfiguring everything?**
A: Use menu options [2] and [3] to change text and vision models individually.

**Q: Can I run the wizard multiple times?**
A: Yes, it detects existing configuration and shows the management menu.

**Q: How do language overrides work?**
A: Language detection happens ONCE per feed domain (not per article). The wizard manages `feed_language_overrides.txt` to force specific languages for specific feeds. Example: Italian tech site → always summarize in English.

**Q: What's the difference between clearing cache and removing overrides?**
A: Clearing cache (option 12) forces re-detection but keeps your manual overrides. Removing overrides (option 11) deletes specific manual settings, falling back to cache or AI detection.

**Q: Can I edit feed_language_overrides.txt manually?**
A: Yes, but the wizard is recommended for safety. Format: `domain = Language` (one per line, # for comments). Wizard provides validation and prevents typos.

**Q: Do language overrides affect feed type detection?**
A: No, these are separate systems. Feed type = comic vs news. Language = which language to summarize in. Both can be overridden independently.

**Q: Why is language detected per feed, not per article?**
A: Massive efficiency gain! Detecting language for 100 articles = 50,000 tokens wasted. Detecting once per feed = 500 tokens. That's a 100x reduction in costs.

**Q: What if a feed changes language over time?**
A: Clear the cache (option 12) to force re-detection. If the feed permanently changed language, you can add a manual override or let AI detect the new language automatically.

**Q: Can I force all feeds to English?**
A: Yes! Add an override for each feed domain pointing to "English". The wizard makes this easy - use option [10] repeatedly for each feed.

**Q: What does "summarize in English" mean for an Italian article?**
A: The system detects the article is Italian, then instructs the AI: "This is Italian content, please provide an English summary." The AI translates and summarizes simultaneously.

**Q: Will clearing cache cost me money?**
A: Yes, a small one-time cost. If you have 10 feeds and clear cache, AI will detect language for each feed on next run (~500 tokens per feed = 5,000 tokens total). After that, it's cached again.

**Q: Can I see what languages are cached?**
A: Not directly in the wizard, but you can view `.feed_language_cache.json` manually. It shows: `{"domain.com": "Italian", ...}`. Cache is auto-managed and gitignored.

**Q: What if I want Italian summaries for an English site?**
A: Add an override: `english-site.com = Italian`. The system will detect English content but instruct the AI to provide Italian summaries. Works for any language combination.
