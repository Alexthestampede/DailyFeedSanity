# AI Provider Guide

The RSS Feed Processor supports multiple AI providers for text summarization, title generation, clickbait detection, and vision processing. This guide explains how to configure and use each provider.

## Supported Providers

1. **Ollama** (local, free) - Default
2. **LM Studio** (local, free)
3. **OpenAI** (cloud, paid)
4. **Google Gemini** (cloud, free tier + paid)
5. **Anthropic Claude** (cloud, paid)

### Future Provider (Research Complete)

6. **Apple MLX** (local, free, Apple Silicon only) - Not yet implemented
   - See [APPLE_AI_INTEGRATION_RESEARCH.md](APPLE_AI_INTEGRATION_RESEARCH.md) for implementation details
   - Estimated integration effort: 4-6 hours
   - Would work like Ollama but optimized for Apple Silicon

## Quick Start

### Using Ollama (Default)

No configuration needed if you're already using Ollama:

```bash
python -m src.main
```

### Switching Providers

**Via Config File** (`src/config.py`):
```python
AI_PROVIDER = 'gemini'  # or 'openai', 'claude', etc.
```

**Via Command Line**:
```bash
python -m src.main --ai-provider gemini
python -m src.main --ai-provider openai
python -m src.main --ai-provider claude
```

## Provider Details

### 1. Ollama (Local)

**Pros:**
- Completely free and local
- No API keys or internet required (after model download)
- Full privacy - data never leaves your machine
- Unlimited usage

**Cons:**
- Requires local setup and model downloads
- Requires GPU for good performance
- Models may not be as capable as cloud providers

**Configuration:**
```python
# src/config.py
AI_PROVIDER = 'ollama'
OLLAMA_BASE_URL = "http://localhost:11434"
TEXT_MODEL = "granite4:tiny-h"  # Your text model
VISION_MODEL = "qwen3-vl:4b"  # Your vision model
```

**Setup:**
1. Install Ollama: https://ollama.com/
2. Pull models: `ollama pull granite4:tiny-h ` (or your preferred model)
3. Run the application

---

### 2. LM Studio (Local)

**Pros:**
- Free and local like Ollama
- Great UI for model management
- OpenAI-compatible API
- Full privacy

**Cons:**
- Requires local setup
- Requires GPU for good performance
- Smaller model selection than Ollama

**Configuration:**
```python
# src/config.py
AI_PROVIDER = 'lm_studio'
LM_STUDIO_BASE_URL = "http://localhost:1234"
LM_STUDIO_TEXT_MODEL = "qwen/qwen3-vl-4b"
LM_STUDIO_VISION_MODEL = "qwen/qwen3-vl-4b"
```

**Setup:**
1. Download LM Studio: https://lmstudio.ai/
2. Download a model (e.g., qwen3-vl-4b for vision support)
3. Start the local server
4. Run the application with `--ai-provider lm_studio`

**Testing:**
```bash
python scripts/test_lm_studio.py
python scripts/test_lm_studio_vision.py /path/to/image.jpg "What's in this image?"
```

---

### 3. OpenAI (Cloud)

**Pros:**
- Most powerful models (GPT-4o, GPT-4o-mini)
- Excellent quality
- Fast and reliable
- Vision support with GPT-4o

**Cons:**
- Requires API key and payment
- Data sent to OpenAI servers
- Costs per API call

**Configuration:**
```python
# src/config.py
AI_PROVIDER = 'openai'
OPENAI_TEXT_MODEL = "gpt-4o-mini"  # Cost-effective
OPENAI_VISION_MODEL = "gpt-4o"  # Vision capable
```

**Setup:**
1. Get API key: https://platform.openai.com/api-keys
2. Set environment variable:
   ```bash
   export OPENAI_API_KEY='sk-your-key-here'
   ```
3. Run the application with `--ai-provider openai`

**Cost Estimates (as of 2024):**
- **gpt-4o-mini**: $0.150/1M input tokens, $0.600/1M output tokens
- **gpt-4o**: $2.50/1M input tokens, $10.00/1M output tokens

Typical daily usage (30 articles + 12 comics with vision):
- Text processing: ~$0.01-0.02/day (gpt-4o-mini)
- Vision processing: ~$0.05-0.10/day (gpt-4o)
- **Total: ~$0.06-0.12/day or ~$2-4/month**

**Testing:**
```bash
python scripts/test_openai_provider.py --test all
```

---

### 4. Google Gemini (Cloud)

**Pros:**
- Very generous free tier
- Excellent quality (Gemini 1.5 Flash/Pro)
- Built-in vision support
- Competitive pricing

**Cons:**
- Requires API key
- Data sent to Google servers
- Some quotas and limits

**Configuration:**
```python
# src/config.py
AI_PROVIDER = 'gemini'
GEMINI_TEXT_MODEL = "gemini-1.5-flash"
GEMINI_VISION_MODEL = "gemini-1.5-flash"  # Same model
```

**Setup:**
1. Get API key: https://aistudio.google.com/app/apikey
2. Set environment variable:
   ```bash
   export GEMINI_API_KEY='your-key-here'
   # or
   export GOOGLE_API_KEY='your-key-here'
   ```
3. Run the application with `--ai-provider gemini`

**Cost:**
- **Free Tier**: 15 requests/minute, 1500 requests/day
- **Paid**: Very low cost, cheaper than OpenAI
- For typical usage, **free tier is usually sufficient**

**Testing:**
```bash
python scripts/test_gemini_provider.py --test all
```

---

### 5. Anthropic Claude (Cloud)

**Pros:**
- Excellent quality and safety
- All Claude 3+ models have vision built-in
- Good context handling
- Ethical AI focus

**Cons:**
- Requires API key and payment
- Data sent to Anthropic servers
- Costs per API call

**Configuration:**
```python
# src/config.py
AI_PROVIDER = 'claude'  # or 'anthropic'
CLAUDE_TEXT_MODEL = "claude-3-5-haiku-20241022"  # Fast & cheap
CLAUDE_VISION_MODEL = "claude-3-5-haiku-20241022"  # Same model
```

**Setup:**
1. Get API key: https://console.anthropic.com/
2. Set environment variable:
   ```bash
   export ANTHROPIC_API_KEY='sk-ant-your-key-here'
   ```
3. Run the application with `--ai-provider claude`

**Cost Estimates (as of 2024):**
- **Claude 3.5 Haiku**: $0.80/1M input, $4.00/1M output (includes vision)
- **Claude 3.5 Sonnet**: $3.00/1M input, $15.00/1M output (best quality)

Typical daily usage:
- **Total: ~$0.08-0.15/day or ~$2.50-4.50/month** (using Haiku)

**Testing:**
```bash
python scripts/test_claude_provider.py --test all
```

---

## Features by Provider

| Feature | Ollama | LM Studio | OpenAI | Gemini | Claude |
|---------|--------|-----------|---------|---------|---------|
| **Text Summarization** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Title Generation** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Clickbait Detection** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Multi-language** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Vision/Image Analysis** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Feed Type Detection** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Cost** | Free | Free | Paid | Free/Paid | Paid |
| **Privacy** | Local | Local | Cloud | Cloud | Cloud |
| **Setup Difficulty** | Medium | Medium | Easy | Easy | Easy |

---

## Choosing a Provider

### Best for Privacy & Cost
**Ollama or LM Studio** - Completely local and free

### Best for Quality (Cloud)
**OpenAI GPT-4o** or **Claude 3.5 Sonnet** - Highest quality, but more expensive

### Best for Budget (Cloud)
**Google Gemini** - Excellent free tier, very cheap paid tier

### Best for Balance (Cloud)
**Gemini 1.5 Flash** or **Claude 3.5 Haiku** - Good quality, reasonable cost

### Best for No Setup
**Google Gemini** - Free tier, instant setup with just an API key

---

## Advanced Configuration

### Mixing Providers

You can use different providers for different purposes by modifying the factory in `src/ai_client/factory.py`. For example:
- Ollama for text summarization (free, local)
- Gemini for vision tasks (free tier sufficient)

### Model Selection

Each provider allows customization of which models to use:

```python
# In src/config.py

# Use faster, cheaper models
OPENAI_TEXT_MODEL = "gpt-4o-mini"  # Instead of gpt-4o
CLAUDE_TEXT_MODEL = "claude-3-5-haiku-20241022"  # Instead of Sonnet

# Use more powerful models for better quality
GEMINI_TEXT_MODEL = "gemini-1.5-pro"  # Instead of Flash
```

### Environment Variables

All API keys should be stored as environment variables for security:

```bash
# Add to your .bashrc or .zshrc
export OPENAI_API_KEY='sk-...'
export GEMINI_API_KEY='...'
export ANTHROPIC_API_KEY='sk-ant-...'
```

Or create a `.env` file:
```bash
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
ANTHROPIC_API_KEY=sk-ant-...
```

---

## Troubleshooting

### Provider Not Working

1. **Check API Key**: Ensure environment variable is set
   ```bash
   echo $OPENAI_API_KEY
   ```

2. **Test Provider**:
   ```bash
   python scripts/test_openai_provider.py --test health
   python scripts/test_gemini_provider.py --test health
   python scripts/test_claude_provider.py --test health
   ```

3. **Check Logs**: Run with `--debug` flag
   ```bash
   python -m src.main --debug --ai-provider gemini
   ```

### Rate Limits

If you hit rate limits:
- **Gemini**: Free tier has 15 requests/minute limit
- **OpenAI/Claude**: Upgrade your tier or wait
- **Solution**: Switch to local provider (Ollama/LM Studio)

### Cost Control

Monitor costs for cloud providers:
- OpenAI: https://platform.openai.com/usage
- Gemini: https://console.cloud.google.com/
- Claude: https://console.anthropic.com/

Use cheaper models for text, reserve powerful models for complex tasks.

---

## Summary

All five providers are fully supported with identical features. Choose based on your priorities:
- **Privacy**: Ollama or LM Studio
- **Cost**: Gemini (free tier) or local providers
- **Quality**: OpenAI or Claude
- **Ease**: Gemini (just need API key)

The application will work identically regardless of which provider you choose!
