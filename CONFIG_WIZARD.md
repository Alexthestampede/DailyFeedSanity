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
  [9] Exit
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
  "ollama_base_url": "http://192.168.2.150:11434",
  "text_model": "G47bLDMC",
  "vision_model": "qwen34bvla",
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
ollama pull llama2
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
ollama pull llama2
ollama pull llava  # Vision model (optional)

# Run wizard
python -m src.utils.config_wizard
# Select [1] Ollama
# Use default URL (http://localhost:11434)
# Select llama2 for text
# Select llava for vision (or skip)
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
