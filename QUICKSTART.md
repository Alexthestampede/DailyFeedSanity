# Quick Start Guide

Get the RSS Feed Processor running in 5 minutes!

## Option 1: Local AI (Ollama) - Privacy First

**Best for**: Privacy, no API costs, offline usage after setup

### Step 1: Install Ollama
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Step 2: Pull a Model
```bash
ollama pull granite4:tiny-h
```

### Step 3: Run
```bash
python -m src.main
```

### Step 4: View Output
Open `output/YYYY-MM-DD/index.html` in your browser!

---

## Option 2: Cloud AI (Gemini) - Easiest Start

**Best for**: Quick setup, generous free tier, excellent quality

### Step 1: Get API Key
Visit https://aistudio.google.com/app/apikey and create a free API key

### Step 2: Set Environment Variable
```bash
export GEMINI_API_KEY='your-key-here'
```

### Step 3: Run
```bash
python -m src.main --ai-provider gemini
```

### Step 4: View Output
Open `output/YYYY-MM-DD/index.html` in your browser!

---

## Next Steps

### Add Your Own Feeds

Edit `rss.txt` and add feed URLs (one per line):
```
https://xkcd.com/rss.xml
https://feeds.feedburner.com/TechCrunch
```

### Try Different Providers

```bash
# Local options
python -m src.main --ai-provider lm_studio

# Cloud options (require API keys)
python -m src.main --ai-provider openai
python -m src.main --ai-provider claude
```

### Common Options

```bash
# Get all news articles (not just last 24 hours)
python -m src.main --all-entries

# Enable debug logging
python -m src.main --debug

# See all options
python -m src.main --help
```

### Fix Feed Classification

If a feed is misclassified, create `feed_type_overrides.txt`:
```
https://wrong-feed.com/rss = news
https://another-feed.com/rss = comic
```

---

## Troubleshooting

### "Ollama server not available"
```bash
# Make sure Ollama is running
ollama serve
```

### "No API key found"
```bash
# Set your API key
export GEMINI_API_KEY='your-key'
export OPENAI_API_KEY='your-key'
export ANTHROPIC_API_KEY='your-key'
```

### Need More Help?

- **Full Documentation**: See [README.md](README.md)
- **AI Provider Details**: See [AI_PROVIDERS.md](AI_PROVIDERS.md)
- **Command Help**: Run `python -m src.main --help`

---

## What's Next?

1. **Customize**: Edit `src/config.py` to change default settings
2. **Schedule**: Set up a cron job to run daily
3. **Explore**: Try different AI providers to find your favorite

Enjoy your personalized daily digest!
