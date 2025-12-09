# RSS Feed Processor

An intelligent RSS feed processor that downloads webcomics and summarizes news articles using AI. Supports multiple AI providers (Ollama, LM Studio, OpenAI, Gemini, Claude) with automatic feed classification, clickbait detection, and multi-language support.

## Features

### Core Functionality
- **Concurrent Processing**: Handles 10+ feeds simultaneously without blocking
- **Smart Feed Detection**: Auto-classifies feeds as comics or news using AI
- **Dual Content Types**:
  - **Webcomics**: Downloads images, validates quality
  - **News Articles**: Extracts text, generates AI summaries and titles

### AI Capabilities
- **5 AI Providers**: Ollama, LM Studio, OpenAI, Gemini, Claude
- **Text Processing**: Summarization, title generation, language detection
- **Vision Processing**: Image validation, comic verification, multi-page detection
- **Clickbait Detection**: AI + author-based detection with special handling
- **Feed-Level Language Detection**: Detects language once per feed (not per article), massive token savings
- **Language Override System**: Force any feed to summarize in any language (e.g., Italian→English)

### User Experience
- **Single HTML Output**: Collapsible summaries, dark mode support
- **24-Hour News Filter**: Only recent articles (configurable)
- **Manual Overrides**: Customize feed classification
- **Flexible Configuration**: CLI args, config file, environment variables

## Quick Start

### 1. Basic Setup (Using Ollama)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull llama2

# Run the processor
python -m src.main
```

**Output**: `output/YYYY-MM-DD/index.html`

### 2. Using Cloud AI (Gemini - Free Tier)

```bash
# Get API key from https://aistudio.google.com/app/apikey
export GEMINI_API_KEY='your-key-here'

# Run with Gemini
python -m src.main --ai-provider gemini
```

### 3. View Help

```bash
python -m src.main --help
```

## Installation

### Requirements
- Python 3.8+
- Internet connection (for feed fetching)
- AI Provider (choose one):
  - **Local**: Ollama or LM Studio
  - **Cloud**: OpenAI, Gemini, or Claude API key

### Setup

```bash
# Clone repository
cd /path/to/RSS_copy_1

# Install dependencies
pip install -r requirements.txt

# (Optional) Set up API keys
export GEMINI_API_KEY='your-key'
export OPENAI_API_KEY='your-key'
export ANTHROPIC_API_KEY='your-key'
```

## Usage

### Basic Commands

```bash
# Default (Ollama, 24-hour news filter)
python -m src.main

# Use different AI provider
python -m src.main --ai-provider gemini
python -m src.main --ai-provider lm_studio
python -m src.main --ai-provider openai

# Get all news articles (not just 24h)
python -m src.main --all-entries

# Enable debug logging
python -m src.main --debug

# Validate images with AI
python -m src.main --validate-images

# Manage configuration (AI provider, feeds, language overrides)
python -m src.utils.config_wizard
```

For more examples and details, run: `python -m src.main --help`

## AI Provider Comparison

| Provider | Type | Cost | Setup | Quality | Vision |
|----------|------|------|-------|---------|--------|
| **Ollama** | Local | Free | Medium | Good | ✅ |
| **LM Studio** | Local | Free | Medium | Good | ✅ |
| **Gemini** | Cloud | Free tier | Easy | Excellent | ✅ |
| **OpenAI** | Cloud | ~$2-4/mo | Easy | Excellent | ✅ |
| **Claude** | Cloud | ~$2.50-4.50/mo | Easy | Excellent | ✅ |

**Recommendation**: Start with **Gemini** (free tier) or **Ollama** (privacy).

See [AI_PROVIDERS.md](AI_PROVIDERS.md) for detailed comparison and setup instructions.

## Output

### HTML Page (`output/YYYY-MM-DD/index.html`)
- **Comics Section**: Images with links to source
- **News Section**: Collapsible summaries with AI-generated titles
- **Clickbait Highlighting**: Yellow border for detected clickbait
- **Dark Mode**: Automatic system preference detection
- **Mobile Friendly**: Responsive design

## Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - 5-minute setup guide
- **[CONFIG_WIZARD.md](CONFIG_WIZARD.md)** - Interactive configuration management
- **[AI_PROVIDERS.md](AI_PROVIDERS.md)** - Detailed provider comparison and setup
- **[LANGUAGE_DETECTION.md](LANGUAGE_DETECTION.md)** - Language detection and override system
- **[CLAUDE.md](CLAUDE.md)** - Developer reference and architecture
- **Help**: `python -m src.main --help`

## Troubleshooting

### Common Issues

**"AI provider not available"**
```bash
# Check provider is running
curl http://localhost:11434/api/tags        # Ollama
curl http://localhost:1234/v1/models        # LM Studio

# Or use cloud provider
python -m src.main --ai-provider gemini
```

**"API key not found"**
```bash
# Set environment variable
export GEMINI_API_KEY='your-key'
```

**"Only getting 1 article from news feed"**
- Check feed is classified as 'news' not 'comic'
- Create override in `feed_type_overrides.txt`

See [AI_PROVIDERS.md](AI_PROVIDERS.md) for more troubleshooting.

## Status

✅ **Fully functional** - Processing 12+ webcomics and 30+ news articles daily  
✅ **5 AI providers** - Ollama, LM Studio, OpenAI, Gemini, Claude  
✅ **Auto-detection** - Feed classification, clickbait detection, language matching  
✅ **Vision support** - Image validation across all providers  
✅ **Dark mode** - System preference support  

---

For questions or issues, see the documentation files or run `python -m src.main --help`.
