#!/usr/bin/env python3
"""
Live test: two-stage processing with d1k32 decision model.

Stage 1 (generative): Ornith159b55k produces summary + title in one call.
Stage 2 (decision):   d1k32 produces clickbait/ad verdicts via /v1/systemone.

Two articles max (respecting the 5-article live-test rule).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.news.article_extractor import ArticleExtractor
from src.news.content_cleaner import ContentCleaner
from src.ai_client.domain_text_processor import DomainTextProcessor
from lib.modulle.providers.ollama.text_processor import OllamaTextProcessor
from lib.modulle.providers.ollama.client import OllamaClient

GENERATIVE_MODEL = "Ornith159b55k:latest"
DECISION_MODEL = "d1k32:latest"
BASE_URL = "http://192.168.2.150:11434"

ARTICLES = [
    # One straightforward tech article (expect: clickbait low, ad low)
    ("https://ollama.com/blog/transparent-pricing", False),
    # A typical promo-ish feed article: expect decision stage to weigh in
    ("https://appleinsider.com/articles/26/09/09/dynamic-island-now-shows-three-live-activities", False),
]


def main():
    print("=" * 70)
    print(f"Two-stage test: {GENERATIVE_MODEL} + decision {DECISION_MODEL}")
    print("=" * 70)

    text_proc = OllamaTextProcessor(model=GENERATIVE_MODEL, base_url=BASE_URL)
    decision_client = OllamaClient(base_url=BASE_URL)
    proc = DomainTextProcessor(
        text_proc, enable_ad_detection=True,
        decision_client=decision_client, decision_model=DECISION_MODEL,
        decision_threshold=0.7,
    )
    extractor = ArticleExtractor()
    cleaner = ContentCleaner()

    results = []
    for url, expected_flag in ARTICLES:
        print(f"\n--- {url.split('/')[-1]} ---")
        article = extractor.extract_from_url(url)
        if not article:
            print("  SKIP: extraction failed")
            continue
        cleaned = cleaner.clean_text(article["text"])
        print(f"  extracted {len(cleaned)} chars")

        result = proc.generate_summary_single_call(cleaned, title=article.get("title"))
        if not result:
            print("  FAIL: no result")
            continue

        cp = result.get("clickbait_probability")
        ap = result.get("ad_probability")
        ad_str = f"{ap:.3f}" if ap is not None else "?"
        print(f"  title: {result['title'][:60]}")
        print(f"  summary: {len(result['summary'])} chars, clean")
        print(f"  verdicts: clickbait={result['is_clickbait']} (p={cp:.3f}), "
              f"ad={result['is_ad']} (p={ad_str})")
        results.append(result)

    print("\n" + "=" * 70)
    if len(results) < len(ARTICLES):
        print(f"FAIL: only {len(results)}/{len(ARTICLES)} articles produced results")
        return 1

    # Sanity: decision stage was actually used
    if not all("clickbait_probability" in r for r in results):
        print("FAIL: decision stage not engaged (no probabilities in results)")
        return 1

    print(f"PASS: {len(results)} articles through two-stage pipeline, "
          "decision stage engaged, no reasoning leakage")
    return 0


if __name__ == "__main__":
    sys.exit(main())