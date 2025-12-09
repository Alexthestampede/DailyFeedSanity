# Language Override Quick Start

Quick reference for managing language overrides in the configuration wizard.

## What Are Language Overrides?

Language overrides let you force specific languages for feeds where AI detection is incorrect or you want consistent language handling.

## Quick Commands

### Run the Wizard
```bash
python -m src.utils.config_wizard
```

### Menu Options

| Option | Action | When to Use |
|--------|--------|-------------|
| **[9]** | View language overrides | Check current settings |
| **[10]** | Add language override | Force language for a feed |
| **[11]** | Remove language override | Delete an override |
| **[12]** | Clear language cache | Force re-detection |

## Common Tasks

### Add Override for Italian News Site

```
Menu: Select [10]
Domain: macitynet.it
Language: Italian
Result: macitynet.it → Italian
```

### Add Override with Full URL

```
Menu: Select [10]
Domain: https://www.macitynet.it/feed/
Language: Italian
Result: macitynet.it → Italian (auto-extracted)
```

### Add Override with Path

```
Menu: Select [10]
Domain: feedburner.com/psblog
Language: Italian
Result: feedburner.com/psblog → Italian (path preserved)
```

### Remove an Override

```
Menu: Select [11]
Choose number from list
Example: Select [2] to remove second override
```

### Force Fresh Detection

```
Menu: Select [12]
Confirm with 'y'
Next run will re-detect all languages
Note: Manual overrides are preserved
```

## File Locations

| File | Purpose | Gitignored |
|------|---------|------------|
| `feed_language_overrides.txt` | Your manual overrides | Yes |
| `.feed_language_cache.json` | AI detection cache | Yes |
| `feed_language_overrides.example.txt` | Example template | No |

## Priority Order

When processing a feed, the system checks in this order:

1. **Manual overrides** (highest priority) ← You control this
2. Hardcoded config
3. Cache
4. AI detection
5. Default (none)

**Your overrides always win!**

## Common Languages

Use these exact names (capitalized):

- English
- Italian
- Spanish
- French
- German
- Chinese
- Japanese
- Portuguese
- Russian
- Arabic

Any language name works, but these are most common.

## Examples by Use Case

### Italian Tech News Sites

```
macitynet.it = Italian
feedburner.com/psblog = Italian
ansa.it = Italian
```

### English Tech Sites

```
9to5mac.com = English
arstechnica.com = English
theverge.com = English
```

### Mixed Language Sites

```
lemonde.fr = French
elpais.com = Spanish
spiegel.de = German
```

## Tips

1. **Domain Format**: Use shortest format that uniquely identifies the feed
   - Good: `macitynet.it`
   - Also works: `www.macitynet.it/feed/` (auto-cleaned)

2. **Language Names**: First letter capitalized, rest lowercase
   - Good: `Italian`
   - Avoid: `italian`, `ITALIAN`, `italian language`

3. **Verification**: Use option [9] to view all overrides before running processor

4. **Testing**: Clear cache [12] after adding overrides to see immediate effect

5. **Backup**: Copy `feed_language_overrides.txt` before making major changes

## Troubleshooting

### Override not working?

1. Check domain matches exactly: `[9] View language overrides`
2. Clear cache: `[12] Clear language cache`
3. Run main processor and check logs
4. Verify file exists: `ls -la feed_language_overrides.txt`

### Can't add override?

1. Check for typos in domain/URL
2. Try simpler domain format (remove www, protocol)
3. Check file permissions
4. Restart wizard

### Changes not appearing?

1. Save changes (wizard auto-saves)
2. Clear cache: `[12] Clear language cache`
3. Run processor: `python -m src.main --debug`
4. Check logs for "Using language override"

## Integration

Language overrides work with:

- ✅ All AI providers (Ollama, LM Studio, OpenAI, Gemini, Claude)
- ✅ Feed type detection (independent systems)
- ✅ Main RSS processor (`python -m src.main`)
- ✅ Debug mode (shows override application)

## Manual Editing (Advanced)

You can edit `feed_language_overrides.txt` directly:

```bash
# Create from template
cp feed_language_overrides.example.txt feed_language_overrides.txt

# Edit with your favorite editor
nano feed_language_overrides.txt

# Format: domain = Language
macitynet.it = Italian
feedburner.com/psblog = Italian
9to5mac.com = English
```

**Recommendation**: Use wizard for safety and validation.

## Quick Test

Test the feature:

```bash
# 1. Run test script
python test_language_wizard.py

# 2. Or test with wizard
python -m src.utils.config_wizard
# Select [10], add test override
# Select [9], verify it appears
# Select [11], remove it
# Select [9], verify it's gone
```

## Support

For detailed documentation, see:
- [CONFIG_WIZARD.md](CONFIG_WIZARD.md) - Full wizard documentation
- [LANGUAGE_OVERRIDE_IMPLEMENTATION.md](LANGUAGE_OVERRIDE_IMPLEMENTATION.md) - Technical details
- [CLAUDE.md](CLAUDE.md) - Project overview

For issues:
1. Check documentation above
2. Run with `--debug` flag
3. Check file permissions
4. Verify file format
