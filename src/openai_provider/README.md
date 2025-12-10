# OpenAI Provider for RSS Feed Processor

This module provides OpenAI API integration for the RSS Feed Processor, enabling text summarization and vision processing using GPT-4 and GPT-3.5-turbo models.

## Features

- **Text Summarization**: Generate article summaries using GPT-4o-mini or GPT-3.5-turbo
- **Title Generation**: Create concise, non-clickbait headlines
- **Clickbait Detection**: AI-powered detection of sensationalized content
- **Vision Processing**: Image analysis using GPT-4 Vision (gpt-4o)
- **Multi-language Support**: Automatically responds in the same language as input

## Setup

### 1. Get an OpenAI API Key

Visit [OpenAI Platform](https://platform.openai.com/api-keys) to create an API key.

### 2. Set Environment Variable

```bash
export OPENAI_API_KEY='sk-your-api-key-here'
```

Or add to your `.bashrc` or `.zshrc`:

```bash
echo 'export OPENAI_API_KEY="sk-your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

### 3. Configure Provider

Edit `src/config.py`:

```python
AI_PROVIDER = 'openai'  # Change from 'ollama' to 'openai'
```

## Usage

Once configured, the OpenAI provider will be used automatically when running the main script:

```bash
# Run with OpenAI provider
python -m src.main

# With debug logging
python -m src.main --debug
```

## Configuration Options

You can customize the models used in `src/config.py`:

```python
# OpenAI Configuration
OPENAI_TEXT_MODEL = "gpt-4o-mini"  # Options: gpt-4o-mini, gpt-3.5-turbo, gpt-4o
OPENAI_VISION_MODEL = "gpt-4o"     # Options: gpt-4o, gpt-4-turbo
```

### Recommended Models

**For Text Summarization:**
- `gpt-4o-mini` - Best balance of cost and quality (recommended)
- `gpt-3.5-turbo` - Lower cost, slightly lower quality
- `gpt-4o` - Highest quality, higher cost

**For Vision Processing:**
- `gpt-4o` - Recommended (vision-capable, good performance)
- `gpt-4-turbo` - Alternative vision model

## Cost Estimates

Based on OpenAI pricing (as of 2024):

### Text Summarization (gpt-4o-mini)
- Input: $0.150 per 1M tokens (~750,000 words)
- Output: $0.600 per 1M tokens (~750,000 words)
- **Typical article**: ~2,000 tokens input, ~300 tokens output = $0.00048 per article
- **Daily digest (34 articles)**: ~$0.016

### Vision Processing (gpt-4o)
- Input: $2.50 per 1M tokens
- Output: $10.00 per 1M tokens
- **Image analysis**: ~1,000 tokens per image = $0.0025 per image
- **12 comic images**: ~$0.03

**Estimated daily cost**: ~$0.05 (text + vision combined)

## API Features

### Text Processing

The OpenAI text processor provides:

- **Clickbait Detection**: Analyzes titles and content for sensationalism
- **Smart Summarization**: Different prompts for clickbait vs. regular articles
- **Title Generation**: Creates clear, informative headlines
- **Language Detection**: Automatically responds in source language

### Vision Processing

The OpenAI vision processor provides:

- **Image Analysis**: General image description and analysis
- **OCR**: Extract text from images
- **Comic Validation**: Verify images are actual comics
- **Multi-page Detection**: For comics with multiple pages (e.g., Oglaf)

## Error Handling

The provider includes robust error handling:

- **Missing API Key**: Clear error message with setup instructions
- **Rate Limiting**: Detects and logs rate limit errors (429)
- **Authentication Errors**: Identifies invalid API keys (401)
- **Timeout Handling**: Configurable timeouts for long requests
- **Graceful Degradation**: Falls back to other providers if configured

## Direct Usage (Advanced)

You can also use the OpenAI provider directly in your code:

```python
from src.openai_provider import OpenAIClient, OpenAITextProcessor, OpenAIVisionProcessor

# Initialize with API key from environment
client = OpenAIClient()
text_processor = OpenAITextProcessor(model="gpt-4o-mini")
vision_processor = OpenAIVisionProcessor(model="gpt-4o")

# Or provide API key explicitly
client = OpenAIClient(api_key="sk-...")
text_processor = OpenAITextProcessor(api_key="sk-...", model="gpt-4o-mini")

# Summarize an article
result = text_processor.summarize_article({
    'text': 'Article content here...',
    'title': 'Article Title',
    'author': 'Author Name',
    'url': 'https://example.com/article'
})

print(result['summary'])
print(result['title'])
print(result['is_clickbait'])

# Analyze an image
analysis = vision_processor.analyze_image(
    '/path/to/image.jpg',
    'Describe this comic in detail.'
)
print(analysis)
```

## Switching Between Providers

The RSS processor supports multiple AI providers. You can switch between them by changing `AI_PROVIDER` in config:

- `'ollama'` - Local Ollama server (free, requires local setup)
- `'lm_studio'` - Local LM Studio server (free, requires local setup)
- `'openai'` - OpenAI API (paid, cloud-based)

Each provider implements the same interface, so switching is seamless.

## Troubleshooting

### "API key not found" Error

Make sure you've set the environment variable:

```bash
echo $OPENAI_API_KEY
```

If empty, set it:

```bash
export OPENAI_API_KEY='sk-your-key-here'
```

### Rate Limit Errors

If you're processing many articles, you may hit rate limits. Solutions:

1. Use `gpt-4o-mini` instead of `gpt-4o` for text (higher rate limits)
2. Add delays between requests (modify `src/config.py`)
3. Upgrade your OpenAI account tier

### High Costs

To reduce costs:

1. Use `gpt-4o-mini` for text summarization (much cheaper than gpt-4o)
2. Use `gpt-3.5-turbo` if quality is acceptable (even cheaper)
3. Limit vision processing to only when needed
4. Reduce `MAX_ARTICLE_LENGTH` in config to send less text

## Architecture

The OpenAI provider follows the same architecture as other providers:

```
openai_provider/
├── __init__.py          # Public exports
├── client.py            # OpenAI API client (implements BaseAIClient)
├── text_processor.py    # Text summarization (implements BaseTextProcessor)
└── vision_processor.py  # Image analysis (similar to OllamaVisionClient)
```

All classes implement the base interfaces defined in `src/ai_client/base.py`, ensuring consistency across providers.

## Security Notes

- Never commit your API key to version control
- Use environment variables for API key storage
- Consider using `.env` files with `python-dotenv` for local development
- Monitor your OpenAI usage dashboard regularly
- Set spending limits in your OpenAI account settings
