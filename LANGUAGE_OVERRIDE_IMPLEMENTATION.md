# Language Override Management Implementation

This document describes the language override management features added to the configuration wizard.

## Overview

The configuration wizard (`src/utils/config_wizard.py`) now provides interactive tools to manage language overrides for RSS feeds. This allows users to force specific languages for feeds where AI detection may be incorrect or inconsistent.

## Files Modified

### 1. `/home/alexthestampede/Aish/RSS copy (1)/src/utils/config_wizard.py`

**Added Constants** (lines 23-24):
```python
LANGUAGE_OVERRIDE_FILE = Path(__file__).parent.parent.parent / 'feed_language_overrides.txt'
LANGUAGE_CACHE_FILE = Path(__file__).parent.parent.parent / '.feed_language_cache.json'
```

**Added Functions** (lines 715-966):

1. **`view_language_overrides()`** (lines 715-761)
   - Displays all configured language overrides in a formatted table
   - Shows helpful message if no overrides exist
   - Handles missing file gracefully
   - Format: `domain → language`

2. **`add_language_override()`** (lines 764-851)
   - Interactive prompt for domain/URL and language
   - Validates and cleans input (extracts domain from URL)
   - Checks for existing overrides and prompts to replace
   - Preserves comments and blank lines in file
   - Creates file if it doesn't exist
   - Returns: `True` if successful, `False` otherwise

3. **`remove_language_override()`** (lines 854-936)
   - Displays numbered list of current overrides
   - Prompts for selection or cancellation
   - Preserves comments when rewriting file
   - Returns: `True` if successful, `False` otherwise

4. **`clear_language_cache()`** (lines 939-966)
   - Deletes `.feed_language_cache.json`
   - Confirms with user before deletion
   - Returns: `True` if successful, `False` otherwise

**Updated Menu** (lines 1037-1203):
- Added 4 new menu options (9-12)
- Updated option numbering (Exit moved to 13)
- Updated prompt to reflect new option count
- Added handlers for all new functions

### 2. `/home/alexthestampede/Aish/RSS copy (1)/CONFIG_WIZARD.md`

**Updated Menu Display** (lines 25-40):
- Added new options to the menu example

**Added Section: Managing Language Overrides** (lines 156-263):
- Complete documentation for all 4 new features
- Examples and use cases
- Priority order explanation
- When to use each feature

**Updated FAQ** (lines 513-523):
- Added 5 new questions about language overrides
- Clarified differences between cache and overrides

## Features

### View Language Overrides (Menu Option 9)

**Displays**:
```
Language Overrides
==================================================

macitynet.it              → Italian
feedburner.com/psblog     → Italian
9to5mac.com               → English
ansa.it                   → Italian

Total: 4 override(s)
```

**Handles**:
- Missing file (shows help message)
- Empty file (shows help message)
- Comments and blank lines (filters them out)

### Add Language Override (Menu Option 10)

**Interactive Steps**:
1. Enter domain or URL (flexible input)
2. Enter language name (with suggestions)

**Features**:
- URL parsing: Extracts domain from full URLs
- Path preservation: Keeps paths like `feedburner.com/psblog`
- Auto-capitalization: Ensures consistent formatting
- Duplicate detection: Prompts to replace existing overrides
- File preservation: Keeps comments and blank lines

**Example Session**:
```
Enter domain or URL: macitynet.it

Common languages: English, Italian, Spanish, French, German, Chinese, Japanese
You can enter any language name.

Enter language: Italian

Language override added: macitynet.it → Italian
```

### Remove Language Override (Menu Option 11)

**Interactive Steps**:
1. Displays numbered list of overrides
2. Prompts for selection (or 'c' to cancel)
3. Removes selected override

**Features**:
- Numbered selection for easy removal
- Cancellation support
- Comment preservation when rewriting file
- Confirmation of what was removed

**Example Session**:
```
Current language overrides:

  [1] macitynet.it → Italian
  [2] feedburner.com/psblog → Italian
  [3] 9to5mac.com → English

Select override to remove [1-3, or 'c' to cancel]: 2

Language override removed: feedburner.com/psblog → Italian
```

### Clear Language Cache (Menu Option 12)

**Interactive Steps**:
1. Explains what will happen
2. Asks for confirmation
3. Deletes cache file

**Features**:
- User confirmation required
- Handles missing cache gracefully
- Clear success/failure messages

**Example Session**:
```
This will force all feed languages to be re-detected on the next run.

Are you sure? [y/N]: y

Language cache cleared successfully.
Languages will be re-detected on next run.
```

## Implementation Details

### URL/Domain Processing

The `add_language_override()` function intelligently handles different input formats:

```python
# Input: macitynet.it
# Output: macitynet.it

# Input: https://macitynet.it/feed
# Output: macitynet.it

# Input: feedburner.com/psblog
# Output: feedburner.com/psblog

# Input: https://feedburner.com/psblog
# Output: feedburner.com/psblog
```

### File Format

The `feed_language_overrides.txt` file format:

```
# This is a comment
# Format: domain = Language

macitynet.it = Italian
feedburner.com/psblog = Italian
9to5mac.com = English

# Another comment
ansa.it = Italian
```

**Rules**:
- One override per line
- Format: `domain = Language`
- Comments start with `#`
- Blank lines ignored
- Language names capitalized

### Error Handling

All functions handle errors gracefully:

1. **Missing files**: Show helpful messages, don't crash
2. **IO errors**: Display error message, return False
3. **Invalid input**: Prompt again or cancel
4. **Empty files**: Treat as no overrides

### Integration with Existing System

The wizard integrates with the existing language override system:

**Priority Order** (from main RSS processor):
1. Manual overrides (`feed_language_overrides.txt`) ← Wizard manages this
2. Hardcoded config (`LANGUAGE_OVERRIDES` in `config.py`)
3. Cache (`.feed_language_cache.json`) ← Wizard can clear this
4. AI detection (automatic)
5. Default to None

**Key Point**: Manual overrides managed by the wizard have **highest priority**.

## Testing

A test script is provided: `/home/alexthestampede/Aish/RSS copy (1)/test_language_wizard.py`

**Tests**:
1. View empty overrides (file doesn't exist)
2. View with data (populated file)
3. Cache file detection
4. Cleanup (removes test files)

**Run**:
```bash
python test_language_wizard.py
```

## Files Created/Modified

### Created:
1. `/home/alexthestampede/Aish/RSS copy (1)/test_language_wizard.py` - Test script

### Modified:
1. `/home/alexthestampede/Aish/RSS copy (1)/src/utils/config_wizard.py` - Core implementation
2. `/home/alexthestampede/Aish/RSS copy (1)/CONFIG_WIZARD.md` - Documentation

### Existing (referenced):
1. `/home/alexthestampede/Aish/RSS copy (1)/feed_language_overrides.example.txt` - Example template
2. `/home/alexthestampede/Aish/RSS copy (1)/feed_language_overrides.txt` - User overrides (gitignored)
3. `/home/alexthestampede/Aish/RSS copy (1)/.feed_language_cache.json` - Cache file (gitignored)

## Usage Example

### Initial Setup

```bash
# Run the wizard
python -m src.utils.config_wizard

# If first time, go through setup
# If already configured, menu appears
```

### Add Language Overrides

```bash
# In the wizard menu:
# Select [10] Add language override
# Enter domain: macitynet.it
# Enter language: Italian
# Repeat for other feeds
```

### View Current Overrides

```bash
# In the wizard menu:
# Select [9] View language overrides
```

### Remove an Override

```bash
# In the wizard menu:
# Select [11] Remove language override
# Select number from list
```

### Clear Cache (Force Re-detection)

```bash
# In the wizard menu:
# Select [12] Clear language cache
# Confirm with 'y'
```

## Best Practices

1. **Use wizard for management**: Safer than manual editing
2. **View before removing**: Check what you're about to delete
3. **Clear cache after changes**: Force immediate re-detection
4. **Test with main processor**: Verify overrides work as expected
5. **Backup important settings**: Copy `feed_language_overrides.txt` before major changes

## Troubleshooting

### "No language overrides configured"
- File doesn't exist or is empty
- Add overrides with menu option [10]

### "Error writing language override"
- Check file permissions
- Ensure directory is writable
- Check disk space

### "Language cache does not exist"
- Cache only created after first run of main processor
- Not an error, just informational

### Changes not taking effect
- Clear cache with menu option [12]
- Verify override format in file
- Check domain matches exactly (case-sensitive)

## Future Enhancements

Potential improvements:
1. Bulk import from CSV file
2. Language validation (check against known languages)
3. Automatic cache clearing after override changes
4. Export overrides to shareable format
5. Integration with feed manager for per-feed editing
