# Quick Start Guide

Get the RSS Feed Processor running in 5 minutes!

## First Time Setup

**macOS/Linux users**: Run the automated setup first:
```bash
./setup.sh  # Creates venv, installs dependencies, runs config wizard
```

**Windows users**: See [README.md](README.md) for manual setup instructions.

---

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

### Step 3: Run Setup (if not done already)
```bash
./setup.sh  # Creates venv and installs dependencies
```

### Step 4: Run the Processor
```bash
./dailyfeedsanity.sh
# OR: source .venv/bin/activate && python -m src.main
```

### Step 5: View Output
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

### Step 3: Run Setup (if not done already)
```bash
./setup.sh  # Creates venv and installs dependencies
```

### Step 4: Configure and Run
```bash
./dailyfeedsanity.sh --config  # Select Gemini in wizard
./dailyfeedsanity.sh
# OR: source .venv/bin/activate && python -m src.main --ai-provider gemini
```

### Step 5: View Output
Open `output/YYYY-MM-DD/index.html` in your browser!

---

## Next Steps

### Add Your Own Feeds

Use the configuration wizard:
```bash
./dailyfeedsanity.sh --config  # Interactive menu to add/manage feeds
```

Or edit `rss.txt` manually and add feed URLs (one per line):
```
https://xkcd.com/rss.xml
https://feeds.feedburner.com/TechCrunch
```

### Try Different Providers

```bash
# Using launcher script
./dailyfeedsanity.sh --ai-provider lm_studio
./dailyfeedsanity.sh --ai-provider openai
./dailyfeedsanity.sh --ai-provider claude

# OR activate venv and use Python directly
source .venv/bin/activate
python -m src.main --ai-provider lm_studio
python -m src.main --ai-provider openai
python -m src.main --ai-provider claude
```

### Common Options

```bash
# Using launcher script
./dailyfeedsanity.sh --all-entries  # Get all news articles (not just last 24 hours)
./dailyfeedsanity.sh --debug        # Enable debug logging
./dailyfeedsanity.sh --help         # See all options

# OR activate venv and use Python directly
source .venv/bin/activate
python -m src.main --all-entries
python -m src.main --debug
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
- **Command Help**: Run `./dailyfeedsanity.sh --help`

---

## What's Next?

1. **Customize**: Edit `src/config.py` to change default settings
2. **Schedule**: Set up a cron job to run daily
3. **Explore**: Try different AI providers to find your favorite

Enjoy your personalized daily digest!
