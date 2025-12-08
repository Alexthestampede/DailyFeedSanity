# Feed Type Override - Quick Start Guide

## Problem: Ollama Classified a Feed Incorrectly

If you see in your logs that a feed was misclassified, you can manually override it.

## Solution: 3 Simple Steps

### Step 1: Create the Override File
```bash
cp feed_type_overrides.example.txt feed_type_overrides.txt
```

### Step 2: Add Your Override
Edit `feed_type_overrides.txt` and add a line:

```
https://your-feed-url.com/rss = comic
```
or
```
https://your-feed-url.com/rss = news
```

### Step 3: Run the Processor
```bash
python -m src.main
```

That's it! Your override is now active.

---

## Examples

### Example 1: Feed Detected as Comic, But It's Actually News
**Log shows:**
```
Classified https://techblog.com/feed as 'comic' (Ollama detection)
```

**Fix:**
```bash
echo "https://techblog.com/feed = news" >> feed_type_overrides.txt
```

### Example 2: Feed Detected as News, But It's Actually a Comic
**Log shows:**
```
Classified https://webcomic.com/rss as 'news' (Ollama detection)
```

**Fix:**
```bash
echo "https://webcomic.com/rss = comic" >> feed_type_overrides.txt
```

---

## Important Notes

1. **URL Must Match Exactly**
   - Use the exact URL from your `rss.txt` file
   - URLs are case-sensitive
   - Include http:// or https://

2. **Type Must Be Valid**
   - Only `comic` or `news` (lowercase)
   - Anything else will be ignored with a warning

3. **Overrides Have Highest Priority**
   - Your manual override beats everything else
   - Even hardcoded configurations in the code
   - Immediate effect (no restart needed)

---

## Checking What's Classified

Run with debug logging to see classifications:
```bash
python -m src.main --debug | grep "Classified"
```

You'll see output like:
```
Classified https://example.com/feed as 'comic' (manual override)
Classified https://another.com/rss as 'news' (from cache)
Classified https://new-feed.com/rss as 'comic' (Ollama detection)
```

---

## File Format

```
# Comments start with hash
# Blank lines are OK

https://feed1.com/rss = comic
https://feed2.com/feed.xml = news

  # Whitespace is trimmed automatically
  https://feed3.com/rss  =  comic
```

---

## Troubleshooting

### Override Not Working?
1. Check the file is named `feed_type_overrides.txt` (not .example.txt)
2. Check the URL matches exactly (copy from rss.txt)
3. Check there are no typos in 'comic' or 'news'
4. Run with --debug to see which classification source is being used

### Want to Remove an Override?
1. Edit `feed_type_overrides.txt`
2. Delete the line or comment it out with #
3. Save the file

### Want to Reset Everything?
```bash
rm feed_type_overrides.txt
```

The system will go back to automatic detection.

---

## Quick Reference

| Task | Command |
|------|---------|
| Create override file | `cp feed_type_overrides.example.txt feed_type_overrides.txt` |
| Add comic override | `echo "URL = comic" >> feed_type_overrides.txt` |
| Add news override | `echo "URL = news" >> feed_type_overrides.txt` |
| Edit overrides | `nano feed_type_overrides.txt` |
| Remove all overrides | `rm feed_type_overrides.txt` |
| See classifications | `python -m src.main --debug \| grep Classified` |

---

## Help

For more details, see:
- `feed_type_overrides.example.txt` - Template with full documentation
- `CLAUDE.md` - Complete project documentation
- `IMPLEMENTATION_SUMMARY.md` - Technical details of this feature
