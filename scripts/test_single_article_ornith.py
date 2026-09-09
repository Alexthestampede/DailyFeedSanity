#!/usr/bin/env python3
"""
Single-article end-to-end test with Ornith159b55k:latest.

Runs the full news pipeline (extract -> clickbait detect -> ad detect ->
summarize -> title) against the remote Ollama server at 192.168.2.150,
then prints a verdict on whether thinking-model cleaning is working.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import requests

from src.news.article_extractor import ArticleExtractor
from src.news.content_cleaner import ContentCleaner
from src.ai_client.domain_text_processor import DomainTextProcessor
from lib.modulle.providers.ollama.client import OllamaClient

MODEL = "Ornith159b55k:latest"
BASE_URL = "http://192.168.2.150:11434"

# Real article from the feed (Appleinsider, short and recent)
TEST_URL = "https://appleinsider.com/articles/26/09/09/dynamic-island-now-shows-three-live-activities"


def main():
    print("=" * 70)
    print(f"Single-article test: {MODEL} @ {BASE_URL}")
    print("=" * 70)

    # 1. Health check
    client = OllamaClient = __import__(
        "lib.modulle.providers.ollama.client", fromlist=["OllamaClient"]
    ).OllamaClient(base_url=BASE_URL)
    if not client.health_check():
        print("FAIL: Ollama server not reachable")
        return 1
    print("Server reachable: OK")

    # 2. Extract article
    extractor = ArticleExtractor()
    article = extractor.extract_from_url(TEST_URL)
    if not article or not article.get("text"):
        print("FAIL: could not extract article text (network or site issue)")
        return 1
    text = article["text"]
    print(f"Extracted {len(text)} chars, title: {article.get('title', '')[:60]}")

    # 3. Clean content
    cleaner = ContentCleaner()
    cleaned = cleaner.clean_text(text)
    validation = cleaner.validate_article_content(cleaned)
    print(f"Content validation: valid={validation['valid']}, words={validation.get('word_count')}")
    if not validation["valid"]:
        print(f"FAIL: content invalid: {validation.get('reason')}")
        return 1

    # 4. Build domain processor against remote server
    class RemoteTextProcessor:
        def generate(self, prompt, system_prompt=None, temperature=0.7, max_tokens=None):
            raw = client.generate(
                model=MODEL,
                prompt=prompt,
                system=system_prompt,
                temperature=temperature,
            )
            if raw:
                print(f"    [model call #{RemoteTextProcessor.n}] raw len={len(raw)}, "
                      f"starts: {raw[:60]!r}")
                RemoteTextProcessor.n += 1
            return raw

    RemoteTextProcessor.n = 1
    proc = DomainTextProcessor(RemoteTextProcessor())

    # 5. Run detection + summary
    print("\n--- Clickbait detection ---")
    is_clickbait = proc.detect_clickbait(cleaned[:500], cleaned)
    print(f"Result: {is_clickbait}")

    print("\n--- Ad detection ---")
    is_ad = proc.detect_ad(cleaned[:500], cleaned)
    print(f"Result: {is_ad}")

    print("\n--- Summary ---")
    result = proc.generate_summary(cleaned, title=article.get("title"))

    if result is None:
        print("FAIL: generate_summary returned None (response rejected)")
        return 1

    print(f"Title: {result['title']}")
    print(f"Summary ({len(result['summary'])} chars): {result['summary']}")
    print(f"clickbait={result['is_clickbait']}, ad={result['is_ad']}")

    # 6. Verdict: check for reasoning leakage
    print("\n" + "=" * 70)
    summary = result["summary"]
    title = result["title"]
    leaks = []
    for marker in ("We need", "Need ", "Let me", "think", "IMPORTANT: You MUST"):
        if marker.lower() in summary.lower() or marker.lower() in title.lower():
            leaks.append(marker)

    if leaks:
        print(f"WARNING: possible reasoning markers in output: {leaks}")
        print("This may be legitimate summary text - inspect manually above.")
        return 2

    print("CLEAN: no reasoning leakage detected in summary or title")
    print("PASS: pipeline works with thinking model")
    return 0


if __name__ == "__main__":
    sys.exit(main())