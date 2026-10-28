#!/usr/bin/env python3
"""
Live test: two-stage processing with d1k32 decision model + pre-filter.

Stage 0 (decision): d1k32 probes every article FIRST (~0.5s) - pure ads
(pre p >= 0.9) are dropped before any generative call.
Stage 1 (generative): Ornith159b55k produces summary + title.
Stage 2 (decision):  d1k32 verdicts from the probe (no second request).

Includes the ollama.com pricing post (previously p(ad)=0.958) to prove
the pre-filter drops it without a summarization call.
"""
import time
from datetime import datetime

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
    # Expected: pre-filter DROP (p(ad) ~0.96) - no generative call
    "https://ollama.com/blog/transparent-pricing",
    # Expected: pre-filter PASS (p(ad) ~0.33) - two-stage processing
    "https://appleinsider.com/articles/26/09/09/dynamic-island-now-shows-three-live-activities",
]


def main():
    print("=" * 70)
    print(f"Pre-filter test: decision {DECISION_MODEL} + generative {GENERATIVE_MODEL}")
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

    stats = {"probed": 0, "dropped": 0, "processed": 0}
    results = []
    for url in ARTICLES:
        name = url.split("/")[-1]
        print(f"\n--- {name} ---")
        t0 = time.time()
        article = extractor.extract_from_url(url)
        if not article:
            print("  SKIP: extraction failed")
            continue
        cleaned = cleaner.clean_text(article["text"])
        t_extract = time.time() - t0

        # Stage 0: probe
        t1 = time.time()
        probe = proc.probe_verdicts(article.get("title"), cleaned)
        t_probe = time.time() - t1
        if not probe:
            print("  FAIL: probe unavailable")
            continue
        stats["probed"] += 1
        print(f"  probe in {t_probe:.1f}s: p(ad)={probe['ad_probability']:.3f}, "
              f"p(clickbait)={probe['clickbait_probability']:.3f}")

        # Route like NewsSummarizer.process_article does
        if probe["ad_probability"] >= 0.9:
            stats["dropped"] += 1
            print(f"  DROPPED pre-filter in {t_extract + t_probe:.1f}s total "
                  f"(generative call skipped)")
            continue

        t2 = time.time()
        result = proc.generate_summary_single_call(
            cleaned, title=article.get("title"), probe=probe)
        t_gen = time.time() - t2
        if not result:
            print("  FAIL: no result")
            continue
        stats["processed"] += 1
        cp = result.get("clickbait_probability")
        ap = result.get("ad_probability")
        cp_str = f"{cp:.3f}" if cp is not None else "generative"
        ad_str = f"{ap:.3f}" if ap is not None else "generative"
        print(f"  processed in {t_gen:.1f}s: clickbait={result['is_clickbait']} "
              f"(p={cp_str}), ad={result['is_ad']} (p={ad_str})")
        print(f"  title: {result['title'][:60]}")
        results.append(result)

    print("\n" + "=" * 70)
    print(f"stats: probed={stats['probed']}, dropped={stats['dropped']}, "
          f"processed={stats['processed']}")
    if stats["dropped"] == 0:
        print("FAIL: expected the pricing post to be dropped pre-filter")
        return 1
    if stats["processed"] == 0:
        print("FAIL: expected the tech article to be processed")
        return 1
    print("PASS: pre-filter dropped pure ad without generative call; "
          "survivor processed via two-stage with probe reuse")
    return 0


if __name__ == "__main__":
    sys.exit(main())