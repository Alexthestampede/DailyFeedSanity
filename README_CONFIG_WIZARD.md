# Configuration Wizard

Interactive setup tool for the RSS Feed Processor.

## Quick Start

```bash
python -m src.utils.config_wizard
```

## What It Does

The Configuration Wizard is an interactive command-line tool that helps you:

1. **Select an AI Provider**
   - Ollama (local, free)
   - LM Studio (local, free)
   - OpenAI (cloud, paid)
   - Google Gemini (cloud, free tier + paid)
   - Anthropic Claude (cloud, paid)

2. **Configure Models**
   - Browse available models on local servers
   - See model details (parameters, context size, vision capability)
   - Get warnings about low-context models
   - Separate text and vision model selection

3. **Manage RSS Feeds**
   - Add new feeds with URL validation
   - Remove existing feeds
   - View all configured feeds
   - Automatically sync with `rss.txt`

4. **Test Connections**
   - Verify AI provider is accessible
   - List available models
   - Validate API keys (for cloud providers)

## First Run

On first run, the wizard guides you through complete setup:

```
Welcome to the RSS Feed Processor configuration wizard!

This tool will help you set up:
  - AI provider for article summarization
  - Text and vision models
  - RSS feed sources

Ready to begin setup? [Y/n]:
```

After setup completes, you can run the main processor:

```bash
python -m src.main
```

## Subsequent Runs

After initial setup, the wizard shows a management menu:

```
Current Configuration
======================================================================
AI Provider: Ollama
Server URL: http://localhost:11434
Text Model: llama2
Vision Model: llava
RSS Feeds: 5 configured

Options:
  [1] Change AI provider
  [2] Change text model
  [3] Change vision model
  [4] Add RSS feed
  [5] Remove RSS feed
  [6] View all feeds
  [7] Test AI connection
  [8] Reset configuration
  [9] Exit
```

## Configuration File

Settings are saved to `.config.json` in the project root:

```json
{
  "ai_provider": "ollama",
  "ollama_base_url": "http://localhost:11434",
  "text_model": "llama2",
  "vision_model": "llava",
  "rss_feeds": [
    "https://example.com/feed1",
    "https://example.com/feed2"
  ],
  "first_run_complete": true
}
```

This file is gitignored for security (contains API keys for cloud providers).

## Features

### Smart Model Selection

**For Ollama:**
- Lists all available models on your server
- Shows detailed information: parameters, size, context window, vision capability
- Filters vision-capable models for vision selection
- Warns about models with context < 4096 tokens
- Optional vision model (can skip)

**For LM Studio:**
- Lists loaded models via OpenAI-compatible API
- Uses same model for text and vision tasks
- Simpler setup process

**For Cloud Providers:**
- Pre-configured optimal models
- Manual override available
- API key secure storage

### URL Validation

When adding RSS feeds:
- Validates URL format (requires scheme and domain)
- Checks for duplicates
- Automatically adds to both `.config.json` and `rss.txt`

### Error Handling

- Graceful connection failure messages
- Rollback on file write errors
- Clear setup instructions for failed connections
- Helpful validation errors

### Security

- API keys stored only in `.config.json` (gitignored)
- Cost warnings before accepting cloud provider setup
- No accidental API calls during testing

## Provider-Specific Setup

### Ollama

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull llama2

# Pull a vision model (optional)
ollama pull llava

# Run wizard
python -m src.utils.config_wizard
```

### LM Studio

```bash
# 1. Download from https://lmstudio.ai/
# 2. Install and open LM Studio
# 3. Download a model (Search tab)
# 4. Load the model (Chat tab)
# 5. Start the server (Server tab)

# Run wizard
python -m src.utils.config_wizard
```

### Cloud Providers

**OpenAI:**
1. Get API key: https://platform.openai.com/api-keys
2. Run wizard and select OpenAI
3. Accept cost warning
4. Enter API key

**Google Gemini (Recommended for beginners):**
1. Get API key: https://aistudio.google.com/app/apikey
2. Run wizard and select Gemini
3. Enter API key
4. Free tier available

**Anthropic Claude:**
1. Get API key: https://console.anthropic.com/
2. Run wizard and select Claude
3. Accept cost warning
4. Enter API key

## Testing

Test the wizard's helper functions:

```bash
python scripts/test_config_wizard.py
```

Tests:
- Configuration load/save
- URL validation
- AI provider definitions
- Connection error handling

## Advanced Usage

### Programmatic Access

Import helper functions in your scripts:

```python
from src.utils.config_wizard import load_config, save_config

# Load user configuration
config = load_config()
if config:
    provider = config['ai_provider']
    text_model = config['text_model']

# Modify and save
config['some_setting'] = 'value'
save_config(config)
```

### Manual Configuration

You can manually edit `.config.json` if needed. The wizard respects manual changes.

### Reset Everything

To start fresh:

```bash
# Delete configuration
rm .config.json

# Run wizard again
python -m src.utils.config_wizard
```

## Troubleshooting

### "Failed to connect to Ollama server"

**Check if Ollama is running:**
```bash
curl http://localhost:11434/api/tags
```

**Start Ollama:**
```bash
ollama serve
```

### "No models found on server"

**For Ollama:**
```bash
# List models
ollama list

# Pull a model
ollama pull llama2
```

**For LM Studio:**
1. Open LM Studio GUI
2. Download a model (Search tab)
3. Load the model (Chat tab)
4. Verify server is running (Server tab)

### "Invalid URL format"

RSS feed URLs must include scheme:
- Good: `https://example.com/feed`
- Bad: `example.com/feed` (missing https://)

### Configuration file corrupt

Delete and recreate:
```bash
rm .config.json
python -m src.utils.config_wizard
```

## FAQ

**Q: Is the wizard required?**
A: No, it's optional. You can still configure via `src/config.py` and command-line arguments.

**Q: Where are API keys stored?**
A: In `.config.json` which is gitignored for security.

**Q: Can I switch providers later?**
A: Yes, use menu option [1]. Your RSS feeds are preserved.

**Q: What if I don't want a vision model?**
A: Vision models are optional for Ollama. Just skip that step.

**Q: Does this modify my code?**
A: No, it only creates/modifies `.config.json` and updates `rss.txt` when adding/removing feeds.

## Documentation

For complete documentation, see:
- **[CONFIG_WIZARD.md](CONFIG_WIZARD.md)** - Full guide with examples and workflows
- **[CLAUDE.md](CLAUDE.md)** - Project overview and architecture
- **[AI_PROVIDERS.md](AI_PROVIDERS.md)** - Detailed AI provider comparison

## Support

If you encounter issues:
1. Check the Troubleshooting section above
2. Read the full documentation in CONFIG_WIZARD.md
3. Run the test suite: `python scripts/test_config_wizard.py`
4. Verify your AI provider is running and accessible
