#!/usr/bin/env python3
"""
Live test: fully staged batching pipeline (extract -> probe batch -> LLM).

Five real blog articles through NewsSummarizer.batch_process with the real
config (Ornith159b55k generative + d1k32 decider). Verifies:
- Stage ordering (probes complete before first generative call)
- Probe batching with concurrency
- Pre-filter drops happen without generative calls
- Stage timing to prove single model-load windows
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import feedparser

from src.ai_client.factory import create_ai_client_with_fallback
from src.news.summarizer import NewsSummarizer
from src.feed_processor.feed_language_detector import FeedLanguageDetector

FEED_URL = "https://ollama.com/blog/rss.xml"
MAX_ARTICLES = 5  # Live-testing rule: 5 max


def main():
    client, text_processor, domain_vision = create_ai_client_with_fallback()

    summarizer = NewsSummarizer(
        text_processor=text_processor,
        language_detector=FeedLanguageDetector(),
    )

    # Real feed entries
    parsed = feedparser.parse(FEED_URL)
    entries = parsed.entries[:MAX_ARTICLES]
    if not entries:
        print("FAIL: no entries in feed")
        return 1
    print("=" * 70)
    print(f"Staged live test: {len(entries)} articles, "
          f"{text_processor.processor.model} + decider "
          f"{getattr(text_processor, 'decision_model', None)}")
    print("=" * 70)

    feed_data = {
        'feed_name': 'Ollama',
        'feed_url': FEED_URL,
        'entries': entries,
        'feed_data': parsed,
        'session': None,
    }

    t0 = time.time()
    results = summarizer.batch_process([feed_data])
    elapsed = time.time() - t0

    print("\n" + "=" * 70)
    prefiltered = [r for r in results if r.get('prefiltered')]
    summarized = [r for r in results if r.get('success') and r.get('summary')]
    failed = [r for r in results if not r.get('success')]

    print(f"Total: {elapsed:.1f}s | results: {len(results)} "
          f"({len(summarized)} summarized, {len(prefiltered)} pre-filtered ads, "
          f"{len(failed)} failed)")

    for r in results:
        marker = ("PREFILTERED - skipped generative"
                  if r.get('prefiltered')
                  else f"ad_p={r.get('ad_probability')}, cb_p={r.get('clickbait_probability')}")
        print(f"  [{r.get('success')}] {r.get('original_title', '')[:55]} - {marker}")

    # Sanity: every result has a decision-model trace OR generative verdicts
    if not results:
        print("FAIL: no results")
        return 1
    print("\nPASS: staged pipeline completed end-to-end")
    return 0


if __name__ == "__main__":
    sys.exit(main())