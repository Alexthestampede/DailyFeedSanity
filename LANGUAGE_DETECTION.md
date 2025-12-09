# Language Detection System

Comprehensive guide to the RSS Feed Processor's feed-level language detection and override system.

## Table of Contents

- [Overview](#overview)
- [How It Works](#how-it-works)
- [Priority System](#priority-system)
- [Managing Overrides](#managing-overrides)
- [Common Use Cases](#common-use-cases)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Technical Details](#technical-details)

---

## Overview

### The Problem

Many RSS feeds publish content in non-English languages. When processing these feeds:

**Without language detection**:
```
Italian tech news site → AI summarizes in Italian → Not helpful for English readers
Chinese forum post → AI summarizes in Chinese → Not helpful for English readers
Multi-language feed → Inconsistent summary languages → Confusing
```

**Traditional per-article solution** (inefficient):
```
Article 1: Detect Italian (500 tokens) → Summarize in English
Article 2: Detect Italian (500 tokens) → Summarize in English
Article 3: Detect Italian (500 tokens) → Summarize in English
...
100 articles = 50,000 tokens wasted on redundant detection
```

### The Solution

**Feed-level language detection** (efficient):
```
Feed domain: macitynet.it
Step 1: Detect language ONCE → Italian (500 tokens)
Step 2: Cache result → .feed_language_cache.json
Step 3: All future articles → Use cached "Italian" → Summarize in English
Result: 500 tokens total (100x reduction!)
```

### Key Benefits

1. **Massive token savings**: 100x reduction in language detection costs
2. **Solves multi-language problems**: Chinese posts on English forums get English summaries
3. **Persistent caching**: Detected once, remembered forever
4. **User control**: Manual overrides for any feed
5. **Automatic**: Works without user intervention

---

## How It Works

### Basic Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Step 1: Extract domain from feed URL                       │
│ https://www.macitynet.it/feed/ → macitynet.it             │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 2: Check priority system (see Priority System section)│
│ Manual override? → Hardcoded? → Cached? → AI detect?      │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 3: Result determined (e.g., "Italian")                │
│ Cached if detected by AI (permanent)                       │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 4: Use language for ALL articles from this feed       │
│ Instruct AI: "Detected Italian, summarize in English"      │
└─────────────────────────────────────────────────────────────┘
```

### Domain Extraction

The system extracts the domain from feed URLs for matching:

| Feed URL | Extracted Domain |
|----------|-----------------|
| `https://www.macitynet.it/feed/` | `macitynet.it` |
| `http://feeds.feedburner.com/psblog` | `feedburner.com/psblog` |
| `https://9to5mac.com/feed/` | `9to5mac.com` |
| `https://www.ansa.it/sito/notizie/mondo/mondo_rss.xml` | `ansa.it` |

**Note**: Subdomains and paths are preserved for specific matching.

### AI Detection Process

When no override or cache exists, the system:

1. Fetches first article from feed
2. Extracts sample text (first 500 characters)
3. Sends to AI provider with prompt:
   ```
   Detect the language of this text. Respond with ONLY the language name.

   Text: [sample text]
   ```
4. AI responds: "Italian"
5. Caches result: `{"macitynet.it": "Italian"}`
6. Uses for all future articles from this feed

**Token cost**: ~500 tokens per feed (one-time)

---

## Priority System

The system checks sources in this order (highest to lowest priority):

### Visual Priority Diagram

```
Feed URL: https://www.macitynet.it/feed/
Domain extracted: macitynet.it

                    ┌──────────────────────────────────┐
                    │  1. Manual Overrides             │
                    │  feed_language_overrides.txt     │
                    │  macitynet.it = English          │
                    └──────────────────────────────────┘
                                 ↓ Found? Use it (DONE)
                                 ↓ Not found? Continue...
                    ┌──────────────────────────────────┐
                    │  2. Hardcoded Config             │
                    │  LANGUAGE_OVERRIDES in config.py │
                    │  Developer defaults              │
                    └──────────────────────────────────┘
                                 ↓ Found? Use it (DONE)
                                 ↓ Not found? Continue...
                    ┌──────────────────────────────────┐
                    │  3. Cache                        │
                    │  .feed_language_cache.json       │
                    │  {"macitynet.it": "Italian"}     │
                    └──────────────────────────────────┘
                                 ↓ Found? Use it (DONE)
                                 ↓ Not found? Continue...
                    ┌──────────────────────────────────┐
                    │  4. AI Detection                 │
                    │  Ask AI to detect language       │
                    │  Cache result for future         │
                    └──────────────────────────────────┘
                                 ↓ Detection successful
                                 ↓ Cache and use (DONE)
                                 ↓ Detection failed? Continue...
                    ┌──────────────────────────────────┐
                    │  5. Default                      │
                    │  None (no language override)     │
                    │  AI decides per article          │
                    └──────────────────────────────────┘
```

### Priority Details

**1. Manual Overrides** (Highest Priority)
- **File**: `feed_language_overrides.txt`
- **Managed by**: Config wizard options [9-12] or manual editing
- **Format**: `domain = Language`
- **Purpose**: User always right! Override any AI detection
- **Scope**: User-specific, gitignored

**2. Hardcoded Config**
- **File**: `src/config.py`
- **Variable**: `LANGUAGE_OVERRIDES`
- **Purpose**: Developer defaults for known problematic feeds
- **Scope**: Project-wide, checked into git

**3. Cache**
- **File**: `.feed_language_cache.json`
- **Managed by**: System (auto-created, auto-updated)
- **Format**: `{"domain": "Language", ...}`
- **Purpose**: Persistent storage of AI detections
- **Scope**: User-specific, gitignored, persistent across runs

**4. AI Detection**
- **Trigger**: First article from unknown feed
- **Method**: Send sample text to AI provider
- **Result**: Cached immediately in `.feed_language_cache.json`
- **Cost**: ~500 tokens per feed (one-time)

**5. Default**
- **Value**: `None` (no language override)
- **Behavior**: AI decides language for each article individually
- **When**: All other methods failed or returned no result

---

## Managing Overrides

### Quick Reference

| Action | Config Wizard Option | Manual Method |
|--------|---------------------|---------------|
| View all overrides | [9] View language overrides | `cat feed_language_overrides.txt` |
| Add override | [10] Add language override | Edit `feed_language_overrides.txt` |
| Remove override | [11] Remove language override | Edit `feed_language_overrides.txt` |
| Clear cache | [12] Clear language cache | `rm .feed_language_cache.json` |

### Using the Config Wizard (Recommended)

**Start the wizard**:
```bash
python -m src.utils.config_wizard
```

**View current overrides** (Option 9):
```
Language Overrides
==================================================

macitynet.it              → English
feedburner.com/psblog     → English
9to5mac.com               → English

Total: 3 override(s)
```

**Add new override** (Option 10):
```
Enter domain or URL: ansa.it

Common languages: English, Italian, Spanish, French, German, Chinese, Japanese
You can enter any language name.

Enter language: English

Language override added: ansa.it → English
```

**Remove override** (Option 11):
```
Current language overrides:

  [1] macitynet.it → English
  [2] feedburner.com/psblog → English
  [3] 9to5mac.com → English

Select override to remove [1-3, or 'c' to cancel]: 2

Override removed: feedburner.com/psblog → English
```

**Clear cache** (Option 12):
```
This will force all feed languages to be re-detected on the next run.

Are you sure? [y/N]: y

Language cache cleared successfully.
Languages will be re-detected on next run.
```

### Manual File Editing

**File location**: `feed_language_overrides.txt` (project root)

**Format**:
```
# Feed Language Overrides
# Format: domain = Language

# Italian tech news sites
macitynet.it = English
ansa.it = English

# Italian PlayStation blog
feedburner.com/psblog = English

# Ensure English summaries even from English sources
9to5mac.com = English
```

**Rules**:
- One override per line
- Format: `domain = Language`
- Lines starting with `#` are comments
- Blank lines ignored
- Language names are case-insensitive but capitalized automatically
- Domain matching is case-sensitive

**Creating the file**:
```bash
# Copy example template
cp feed_language_overrides.example.txt feed_language_overrides.txt

# Or create from scratch
nano feed_language_overrides.txt
```

### Cache Management

**Cache file**: `.feed_language_cache.json` (auto-managed)

**Format**:
```json
{
  "macitynet.it": "Italian",
  "9to5mac.com": "English",
  "feedburner.com/psblog": "Italian"
}
```

**Important**:
- Auto-created on first AI detection
- Auto-updated when new feeds detected
- Gitignored (user-specific)
- Persistent across runs
- Not meant for manual editing (use overrides instead)

**Clear cache**:
```bash
# Using wizard (recommended)
python -m src.utils.config_wizard
# Select [12] Clear language cache

# Or manually
rm .feed_language_cache.json
```

---

## Common Use Cases

### Use Case 1: Italian Tech News → English Summaries

**Scenario**:
- Feed: https://www.macitynet.it/feed/
- Content: Italian tech news articles
- Problem: AI summarizes in Italian (not helpful for English readers)
- Goal: Get English summaries

**Solution**:
```bash
# Using wizard (recommended)
python -m src.utils.config_wizard
# [10] Add language override
# Domain: macitynet.it
# Language: English

# Or manually
echo "macitynet.it = English" >> feed_language_overrides.txt
```

**Result**:
```
Before: Italian article → Summary in Italian
After:  Italian article → Summary in English ✓
```

### Use Case 2: Chinese Leaker on English Forum

**Scenario**:
- Feed: https://forum.example.com/rss
- Content: Mix of English posts and Chinese leaker posts
- Problem: Chinese posts get Chinese summaries, English posts get English summaries (inconsistent)
- Goal: Always get English summaries regardless of post language

**Solution**:
```bash
# Force all posts to English
python -m src.utils.config_wizard
# [10] Add language override
# Domain: forum.example.com
# Language: English
```

**Result**:
```
Before: English post → English summary, Chinese post → Chinese summary
After:  English post → English summary, Chinese post → English summary ✓
```

### Use Case 3: Multi-Language News Feed

**Scenario**:
- Feed: https://international-news.com/feed
- Content: Articles in English, Spanish, and French
- Problem: Summaries in random languages (whatever the article is in)
- Goal: Consistent English summaries for all articles

**Solution**:
```bash
echo "international-news.com = English" >> feed_language_overrides.txt
```

**Result**:
```
All articles summarized in English regardless of source language ✓
```

### Use Case 4: Force English for All Feeds

**Scenario**:
- Have 10+ feeds in various languages
- Goal: All summaries in English for easy reading

**Solution**:
```bash
# Use wizard to add override for each feed
python -m src.utils.config_wizard
# [10] Add language override (repeat for each feed)
# Domain: feed1-domain.com → English
# Domain: feed2-domain.com → English
# etc.
```

**Or create file manually**:
```bash
cat > feed_language_overrides.txt << 'EOF'
# Force all feeds to English
macitynet.it = English
ansa.it = English
lemonde.fr = English
elpais.com = English
spiegel.de = English
asahi.com = English
chinadaily.com.cn = English
EOF
```

### Use Case 5: Test AI Detection Accuracy

**Scenario**:
- Curious what language AI detects for each feed
- Want to verify detection before adding overrides

**Solution**:
```bash
# Clear cache to force fresh detection
python -m src.utils.config_wizard
# [12] Clear language cache

# Run processor with debug logging
python -m src.main --debug

# Check logs for detection results
# Look for: "Language detected for domain.com: Italian"
```

**Review results, then add overrides if needed**.

### Use Case 6: English Site → Italian Summaries

**Scenario**:
- Feed: English tech news site
- Reader: Italian speaker who prefers Italian summaries
- Goal: Translate English articles to Italian

**Solution**:
```bash
echo "english-tech-site.com = Italian" >> feed_language_overrides.txt
```

**Result**:
```
English article → AI detects English → Summarizes in Italian ✓
```

---

## Troubleshooting

### Articles Summarized in Wrong Language

**Symptom**: macitynet.it articles appear in Italian instead of English

**Diagnosis**:
```bash
# Check if override exists
python -m src.utils.config_wizard
# [9] View language overrides
# Look for macitynet.it in the list

# Check logs for detection
python -m src.main --debug | grep "Language"
# Look for: "Language for macitynet.it: Italian"
```

**Solutions**:

1. **Add manual override** (recommended):
   ```bash
   python -m src.utils.config_wizard
   # [10] Add language override
   # Domain: macitynet.it
   # Language: English
   ```

2. **Clear cache and retry**:
   ```bash
   python -m src.utils.config_wizard
   # [12] Clear language cache
   # Run processor again
   ```

### Language Detection Failed

**Symptom**: Logs show "Language detection failed for domain.com"

**Causes**:
- AI provider unavailable
- Network issues
- Invalid feed content
- AI model error

**Solutions**:

1. **Check AI provider**:
   ```bash
   python -m src.utils.config_wizard
   # [7] Test AI connection
   ```

2. **Add manual override** (bypass detection):
   ```bash
   python -m src.utils.config_wizard
   # [10] Add language override
   # Domain: problem-feed.com
   # Language: English
   ```

3. **Run with debug logging**:
   ```bash
   python -m src.main --debug
   # Review detailed error messages
   ```

### Wrong Language Cached

**Symptom**: AI detected Spanish but feed is actually Portuguese

**Solutions**:

1. **Clear cache and let AI retry**:
   ```bash
   python -m src.utils.config_wizard
   # [12] Clear language cache
   python -m src.main --debug
   # Check new detection in logs
   ```

2. **Add manual override** (if AI keeps getting it wrong):
   ```bash
   python -m src.utils.config_wizard
   # [10] Add language override
   # Domain: problem-feed.com
   # Language: Portuguese
   ```

### Override Not Working

**Symptom**: Added override but summaries still in wrong language

**Diagnosis**:
```bash
# 1. Verify override was added
python -m src.utils.config_wizard
# [9] View language overrides
# Confirm the override appears in list

# 2. Check file syntax
cat feed_language_overrides.txt
# Look for typos, wrong format, etc.

# 3. Run with debug logging
python -m src.main --debug | grep "Override"
# Look for: "Language override for domain.com: English"
```

**Common issues**:
- Typo in domain name (case-sensitive!)
- Wrong file format (`domain = Language` not `domain: Language`)
- File not in project root
- Override for wrong domain (check extracted domain in logs)

**Solutions**:
1. Fix typos in `feed_language_overrides.txt`
2. Use wizard to add override (handles validation)
3. Check logs to see extracted domain name

### All Summaries in Wrong Language

**Symptom**: Every feed summarized in Chinese (or other unexpected language)

**Diagnosis**:
```bash
# Check if there's a global override
python -m src.utils.config_wizard
# [9] View language overrides
# Look for unexpected overrides

# Check config.py for hardcoded overrides
grep -r "LANGUAGE_OVERRIDES" src/config.py
```

**Solutions**:
1. Remove incorrect overrides (wizard option [11])
2. Clear cache and retry (wizard option [12])
3. Check AI provider language setting

### Cache File Corrupted

**Symptom**: JSON decode errors, language detection failing

**Solution**:
```bash
# Delete corrupted cache
rm .feed_language_cache.json

# Or use wizard
python -m src.utils.config_wizard
# [12] Clear language cache
```

### Token Costs Too High

**Symptom**: Spending too many tokens on language detection

**Diagnosis**:
```bash
# Check if cache exists
ls -la .feed_language_cache.json

# Check number of cached feeds
cat .feed_language_cache.json | python -m json.tool

# Compare to number of feeds
wc -l rss.txt
```

**Solutions**:

1. **Let cache build up**: First run expensive, subsequent runs free
2. **Add manual overrides**: 0 tokens (no detection needed)
3. **Use local AI provider**: Free for Ollama/LM Studio
4. **Check for cache clearing**: Don't clear cache unnecessarily

**Expected costs**:
- First run (no cache): ~500 tokens × N feeds
- Subsequent runs: 0 tokens (all cached)
- With overrides: 0 tokens (no detection)

---

## FAQ

### General Questions

**Q: How does language detection work?**

A: The system detects language ONCE per feed domain (not per article). It sends a sample of text from the first article to the AI, which responds with the language name (e.g., "Italian"). This result is cached permanently.

**Q: Why feed-level instead of per-article?**

A: Efficiency! Detecting language for 100 articles = 50,000 tokens wasted. Detecting once per feed = 500 tokens. That's a 100x reduction in costs. Plus, most feeds are consistent in language.

**Q: What if a feed has multiple languages?**

A: Use a manual override to force a specific language. Example: Mixed English/Chinese feed → Override to "English" → All articles summarized in English regardless of source language.

**Q: Does this cost extra tokens?**

A: First detection: Yes (~500 tokens per feed, one-time). Subsequent runs: No (cached). With manual overrides: No (skips detection entirely).

### Overrides

**Q: What's the difference between cache and overrides?**

A:
- **Cache**: Auto-managed, AI detections stored here, can be cleared
- **Overrides**: User-managed, manually specified languages, never auto-cleared
- Priority: Overrides always win over cache

**Q: Can I override AI detection?**

A: Yes! That's the whole point. Manual overrides have highest priority. AI detected wrong? Add an override.

**Q: Do I need to restart after adding override?**

A: No. Overrides are checked on every article processing. Next run will use new override immediately.

**Q: Can I use partial domain matching?**

A: No, matching is exact. Use:
- `macitynet.it` (matches macitynet.it and www.macitynet.it)
- `feedburner.com/psblog` (matches that specific feed path)
- Full URL if you need exact matching

### Language Specification

**Q: What do I enter for the language?**

A: Enter the language you want **summaries in**, NOT the source language.
- Italian site → Enter "English" to get English summaries
- Chinese forum → Enter "English" to get English summaries

**Q: What language names are supported?**

A: Any language name! Common: English, Italian, Spanish, French, German, Chinese, Japanese, Korean, Portuguese, Russian, Arabic, Hindi. The AI understands all major languages.

**Q: Is language name case-sensitive?**

A: No, but it's auto-capitalized for consistency. "english" → "English", "ITALIAN" → "Italian".

**Q: Can I use language codes instead of names?**

A: Not recommended. Use full names ("English" not "en") for clarity. The system works with names, not codes.

### Cache Management

**Q: Where is the cache stored?**

A: `.feed_language_cache.json` in the project root. It's auto-managed and gitignored.

**Q: Can I edit the cache manually?**

A: Not recommended. Use manual overrides instead. If you must, it's JSON format: `{"domain": "Language"}`.

**Q: When should I clear the cache?**

A:
- AI detection was wrong and you want it to retry
- Feed changed language (Italian site now English)
- Testing/debugging
- Never clear just because (cached = free, re-detection = costs tokens)

**Q: What happens after clearing cache?**

A: Next run will detect language for all feeds again (~500 tokens per feed). Results are cached again for future runs.

**Q: Does clearing cache delete overrides?**

A: No! Overrides are in a separate file (`feed_language_overrides.txt`). Clearing cache only deletes AI detections.

### Cost and Performance

**Q: How much does language detection cost?**

A: ~500 tokens per feed, one-time. Example: 10 feeds × 500 tokens = 5,000 tokens total on first run. Subsequent runs: 0 tokens (cached).

**Q: Is it cheaper to use overrides?**

A: Yes! Overrides skip detection entirely = 0 tokens. If you know you want English for everything, add overrides for all feeds.

**Q: Does this slow down processing?**

A: First detection: Slight delay (AI query). Subsequent runs: No delay (instant cache lookup).

**Q: Can I disable language detection?**

A: Yes, by not adding any overrides and clearing cache. System will fall back to default behavior (AI decides per article). But this wastes tokens.

### Behavior

**Q: What if language detection fails?**

A: Falls back to default: None (AI decides per article). You'll see a warning in logs. Add manual override to bypass detection.

**Q: Can I force English for some feeds and Italian for others?**

A: Yes! Add separate overrides:
```
feed1.com = English
feed2.com = Italian
feed3.com = Spanish
```

**Q: What happens with English feeds?**

A: If detected as English or overridden to English, the AI gets context that the article is in English and should summarize in English. Same result, but explicit instruction.

**Q: Does this affect feed type detection?**

A: No, these are separate systems. Feed type = comic vs news. Language = which language to summarize in. Both work independently.

### Technical

**Q: How is domain extracted from URL?**

A: The system removes protocol (`http://`, `https://`) and `www.` prefix, then uses the remainder. Example: `https://www.macitynet.it/feed/` → `macitynet.it`.

**Q: What if a feed URL changes?**

A: Cache uses old domain. Either clear cache to re-detect, or add override with new domain.

**Q: Can I see what's cached?**

A: Yes, view `.feed_language_cache.json`:
```bash
cat .feed_language_cache.json | python -m json.tool
```

**Q: Does this work with all AI providers?**

A: Yes! Ollama, LM Studio, OpenAI, Gemini, and Claude all support language detection.

---

## Technical Details

### System Architecture

**Components**:
1. `src/feed_processor/language_detector.py` - Core detection logic
2. `src/utils/language_override_manager.py` - Override file management
3. `.feed_language_cache.json` - Persistent cache storage
4. `feed_language_overrides.txt` - User override configuration

**Flow**:
```python
# Pseudocode
def get_feed_language(feed_url):
    domain = extract_domain(feed_url)

    # Priority 1: Manual overrides
    if domain in manual_overrides:
        return manual_overrides[domain]

    # Priority 2: Hardcoded config
    if domain in LANGUAGE_OVERRIDES:
        return LANGUAGE_OVERRIDES[domain]

    # Priority 3: Cache
    if domain in cache:
        return cache[domain]

    # Priority 4: AI detection
    detected = detect_language_with_ai(feed_url)
    if detected:
        cache[domain] = detected
        save_cache()
        return detected

    # Priority 5: Default
    return None
```

### Cache File Format

**Location**: `.feed_language_cache.json`

**Structure**:
```json
{
  "macitynet.it": "Italian",
  "9to5mac.com": "English",
  "feedburner.com/psblog": "Italian",
  "ansa.it": "Italian",
  "lemonde.fr": "French"
}
```

**Management**:
- Auto-created on first detection
- Auto-updated when new feeds detected
- Never auto-deleted (persistent)
- Manually clearable via wizard or `rm` command

### Override File Format

**Location**: `feed_language_overrides.txt`

**Structure**:
```
# Comments start with #
# Blank lines ignored

# Format: domain = Language
macitynet.it = English
feedburner.com/psblog = English

# You can use full URLs too
https://www.ansa.it/feed/ = English

# Or domain with path
9to5mac.com/feed = English
```

**Parsing rules**:
- Strip whitespace
- Ignore lines starting with `#`
- Ignore blank lines
- Split on `=` (first occurrence)
- Capitalize language name
- Validate format (warn on invalid lines)

### Domain Extraction

**Algorithm**:
```python
def extract_domain(url):
    # Remove protocol
    url = url.replace('http://', '').replace('https://', '')

    # Remove www. prefix
    url = url.replace('www.', '')

    # Remove trailing slash
    url = url.rstrip('/')

    # Keep domain and path
    return url
```

**Examples**:
| Input | Output |
|-------|--------|
| `https://www.macitynet.it/feed/` | `macitynet.it/feed` |
| `http://feeds.feedburner.com/psblog` | `feeds.feedburner.com/psblog` |
| `https://9to5mac.com/` | `9to5mac.com` |

**Note**: Actual implementation may vary slightly. Check `src/feed_processor/language_detector.py` for exact logic.

### AI Detection Prompt

**Template**:
```
Detect the language of this text. Respond with ONLY the language name (e.g., "English", "Italian", "Spanish").

Text: {sample_text}
```

**Sample text**:
- First 500 characters from first article
- Includes title and summary/description
- HTML stripped if present

**Expected response**:
```
Italian
```

**Token cost**: ~500 tokens (sample text + prompt + response)

### Integration Points

**Where language is used**:
1. `src/news/summarizer.py` - Summarization prompts
2. `src/news/article_processor.py` - Article processing
3. `src/ollama_client/` - AI provider integration
4. Logs - Debug information

**Example usage in summarization**:
```python
if feed_language:
    prompt = f"This article is in {feed_language}. Please provide an English summary."
else:
    prompt = "Please summarize this article."
```

---

## Best Practices

### For Users

1. **Use overrides for known feeds**: If you know macitynet.it is Italian, add override immediately (saves tokens)
2. **Let cache build up**: First run expensive, subsequent runs free
3. **Use wizard for management**: Safer than manual editing, includes validation
4. **Check logs occasionally**: Verify detections are accurate
5. **Don't clear cache unnecessarily**: Cached = free, re-detection = costs tokens

### For Developers

1. **Prefer feed-level detection**: Don't add per-article detection
2. **Cache aggressively**: Store any detection immediately
3. **Respect priority order**: Manual overrides always highest priority
4. **Handle failures gracefully**: Fall back to None if detection fails
5. **Log detections**: Help users verify accuracy

### Token Optimization

**Best case** (minimum tokens):
- Add manual overrides for all feeds: 0 tokens

**Good case** (one-time cost):
- Let AI detect once, cache forever: 500 tokens × N feeds (one-time)

**Worst case** (avoid this):
- Clear cache on every run: 500 tokens × N feeds × every run

**Recommendation**: Add overrides for feeds you know, let AI detect unknowns, never clear cache unless needed.

---

## Additional Resources

- **[CONFIG_WIZARD.md](CONFIG_WIZARD.md)** - Interactive override management guide
- **[CLAUDE.md](CLAUDE.md)** - Developer architecture reference
- **[AI_PROVIDERS.md](AI_PROVIDERS.md)** - AI provider comparison and costs
- **Config wizard**: `python -m src.utils.config_wizard`
- **Main processor**: `python -m src.main --help`

---

*Last updated: 2025-12-09*
