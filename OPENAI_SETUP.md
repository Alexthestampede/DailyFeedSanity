# OpenAI Provider - Quick Start Guide

This guide will help you set up and use the OpenAI provider for the RSS Feed Processor.

## What's New

The RSS Feed Processor now supports OpenAI's GPT models as an alternative to Ollama and LM Studio. This provides:

- **Cloud-based processing**: No need for local AI models
- **High-quality summaries**: Using GPT-4o-mini or GPT-4o
- **Vision capabilities**: Image analysis with GPT-4 Vision
- **Multi-language support**: Automatic language detection and matching
- **Reliable performance**: Enterprise-grade API with high uptime

## Prerequisites

1. An OpenAI account
2. An API key with billing enabled

## Setup Steps

### Step 1: Get Your OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key (it starts with `sk-`)
5. **Important**: Save this key securely - you won't be able to see it again

### Step 2: Set Environment Variable

**Linux/Mac:**
```bash
export OPENAI_API_KEY='sk-your-key-here'
```

To make it permanent, add to `~/.bashrc` or `~/.zshrc`:
```bash
echo 'export OPENAI_API_KEY="sk-your-key-here"' >> ~/.bashrc
source ~/.bashrc
```

**Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY = "sk-your-key-here"
```

**Windows (Command Prompt):**
```cmd
set OPENAI_API_KEY=sk-your-key-here
```

### Step 3: Configure the Provider

Edit `/home/alexthestampede/Aish/RSS copy (1)/src/config.py`:

```python
# Change this line:
AI_PROVIDER = 'ollama'

# To this:
AI_PROVIDER = 'openai'
```

### Step 4: Test the Setup

Run the test script to verify everything works:

```bash
cd "/home/alexthestampede/Aish/RSS copy (1)"

# Test API connection
python scripts/test_openai_provider.py --test health

# Test text summarization
python scripts/test_openai_provider.py --test text

# Test all features
python scripts/test_openai_provider.py --test all
```

### Step 5: Run the RSS Processor

```bash
# Run normally
python -m src.main

# With debug logging
python -m src.main --debug
```

## Configuration Options

### Model Selection

Edit `/home/alexthestampede/Aish/RSS copy (1)/src/config.py` to customize models:

```python
# Text summarization model
OPENAI_TEXT_MODEL = "gpt-4o-mini"  # Default (recommended)
# Options: gpt-4o-mini, gpt-3.5-turbo, gpt-4o

# Vision processing model
OPENAI_VISION_MODEL = "gpt-4o"     # Default (recommended)
# Options: gpt-4o, gpt-4-turbo
```

### Cost-Effective Configuration

For minimal cost:
```python
OPENAI_TEXT_MODEL = "gpt-4o-mini"  # Best value
OPENAI_VISION_MODEL = "gpt-4o"     # Only when needed
```

For highest quality:
```python
OPENAI_TEXT_MODEL = "gpt-4o"       # Best quality
OPENAI_VISION_MODEL = "gpt-4o"     # Best vision
```

## Cost Breakdown

Based on typical daily usage (34 news articles + 12 comic images):

### Using gpt-4o-mini (Recommended)
- **Text processing**: ~$0.016/day
- **Vision processing**: ~$0.03/day
- **Total**: ~$0.05/day (~$1.50/month)

### Using gpt-4o for everything
- **Text processing**: ~$0.30/day
- **Vision processing**: ~$0.03/day
- **Total**: ~$0.33/day (~$10/month)

### Tips to Reduce Costs
1. Use `gpt-4o-mini` for text (much cheaper, still high quality)
2. Only use vision processing when necessary
3. Set spending limits in OpenAI dashboard
4. Monitor usage at https://platform.openai.com/usage

## Features

### Text Processing
- Article summarization (100-300 words)
- Non-clickbait title generation
- Clickbait detection and special handling
- Multi-language support (Italian, English, etc.)

### Vision Processing
- Comic image validation
- Multi-page comic detection (Oglaf)
- OCR for text extraction
- Image description and analysis

## Troubleshooting

### Error: "API key not found"

**Solution**: Make sure you've set the environment variable:
```bash
echo $OPENAI_API_KEY
```

If it's empty, set it again and restart your terminal.

### Error: "Authentication failed"

**Causes**:
- Invalid API key
- API key not activated
- Billing not enabled

**Solution**:
1. Verify your API key at https://platform.openai.com/api-keys
2. Check billing at https://platform.openai.com/account/billing
3. Ensure you have credits or payment method set up

### Error: "Rate limit exceeded"

**Solution**:
1. Wait a few minutes and try again
2. Upgrade your OpenAI tier for higher rate limits
3. Use `gpt-4o-mini` (has higher rate limits than gpt-4o)

### High Costs

**Solution**:
1. Switch to `gpt-4o-mini` for text processing
2. Review your usage at https://platform.openai.com/usage
3. Set usage limits in OpenAI settings
4. Consider using Ollama (free, local) for high-volume processing

## Switching Back to Ollama/LM Studio

To switch back to local providers, edit `/home/alexthestampede/Aish/RSS copy (1)/src/config.py`:

```python
# For Ollama
AI_PROVIDER = 'ollama'

# For LM Studio
AI_PROVIDER = 'lm_studio'
```

## Advanced Usage

### Using OpenAI Provider Directly

```python
from src.openai_provider import OpenAITextProcessor, OpenAIVisionProcessor

# Text processing
processor = OpenAITextProcessor(model="gpt-4o-mini")
result = processor.summarize_article({
    'text': 'Article content...',
    'title': 'Article title',
    'author': 'Author name',
    'url': 'https://example.com'
})

# Vision processing
vision = OpenAIVisionProcessor(model="gpt-4o")
description = vision.analyze_image(
    '/path/to/image.jpg',
    'Describe this comic.'
)
```

### Custom API Key per Request

```python
# Use different API key without changing environment
processor = OpenAITextProcessor(
    api_key="sk-different-key",
    model="gpt-4o-mini"
)
```

## Security Best Practices

1. **Never commit API keys** to version control
2. **Use environment variables** for API key storage
3. **Set spending limits** in OpenAI dashboard
4. **Monitor usage regularly** to detect unusual activity
5. **Rotate keys** if you suspect compromise
6. **Use separate keys** for development and production

## Support & Resources

- **OpenAI Documentation**: https://platform.openai.com/docs
- **API Reference**: https://platform.openai.com/docs/api-reference
- **Pricing**: https://openai.com/pricing
- **Status Page**: https://status.openai.com
- **Community**: https://community.openai.com

## Implementation Details

The OpenAI provider is located in `/home/alexthestampede/Aish/RSS copy (1)/src/openai_provider/`:

```
openai_provider/
├── __init__.py          # Public exports
├── client.py            # OpenAI API client
├── text_processor.py    # Text summarization
├── vision_processor.py  # Image analysis
└── README.md           # Detailed documentation
```

All components implement the same interfaces as Ollama and LM Studio, ensuring seamless switching between providers.

## Next Steps

1. ✓ Set up API key
2. ✓ Configure provider in config.py
3. ✓ Test with test script
4. ✓ Run full RSS processor
5. Monitor costs and adjust models as needed
6. Set spending limits in OpenAI dashboard

Enjoy your new cloud-powered RSS feed processor!
