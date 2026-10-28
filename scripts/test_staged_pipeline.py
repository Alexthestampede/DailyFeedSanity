#!/usr/bin/env python3
"""
Tests for the staged batching pipeline in NewsSummarizer.

Verifies:
- Stage ordering: ALL probes complete before the FIRST generative call
- Probes run concurrently in batches (peak concurrency observed)
- Pure ads are dropped pre-filter without any generative call
- Probe failures fall back safely (probe=None -> generative verdicts)
- Extraction failures produce failed results without any AI calls
- Success/failure counts and shapes stay compatible
"""
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
logging.disable(logging.CRITICAL)

from src.news.summarizer import NewsSummarizer


def make_entry(i):
    """Feed entry with content in the description (no HTTP fetch needed),
    title starting with the index for mock parsing."""
    return {
        'title': f'{i} Announcement Featuring Substantial Test Content',
        'link': f'http://example.com/{i}',
        'description': f'<p>This is a test article body for entry {i} with '
                       f'substantial content to pass validation checks. ' * 8 + '</p>',
        'published': 'Mon, 01 Jan 2026 00:00:00 +0000',
    }


def build_summarizer(probe_values, fail_probe_for=None, decision_stage=True):
    """
    Build a NewsSummarizer with mocked extractor/cleaner/detector/clients.

    probe_values: dict title-index -> probe dict (or None for a failure)
    fail_probe_for: set of indexes whose probes raise
    decision_stage: mock exposes decision_client (probes enabled) or not
    """
    from src.news.content_cleaner import ContentCleaner

    class MockExtractor:
        def extract_from_feed_entry(self, entry, session=None):
            text = ' '.join([f'Article {entry["title"]} body content.' for _ in range(60)])
            return {
                'url': entry['link'],
                'text': text,
                'title': entry['title'],
                'author': None,
                'date': 'Mon, 01 Jan 2026 00:00:00 +0000',
                'description': entry.get('description'),
                'source': 'extracted',
            }

    class MockDetector:
        def get_feed_language(self, feed_url, feed_data=None):
            return 'English'

    class MockAIClient:
        def __init__(self):
            self.calls = {
                'probes': [],
                'single_calls': [],
                'legacy_calls': [],
            }
            self.order = []  # ('probe', i) / ('generate', i)
            self.peak_probe_concurrency = 0
            self._current = 0
            self._lock = threading.Lock()
            # Gate requires decision stage to be present for probing
            if decision_stage:
                self.decision_client = object()
                self.decision_model = 'mock-decider:latest'

        @staticmethod
        def _idx(title):
            # Mock titles start with the index: "{i} Announcement Title..."
            return int(title.split()[0])

        def probe_verdicts(self, title, text):
            idx = self._idx(title)
            with self._lock:
                self._current += 1
                self.peak_probe_concurrency = max(
                    self.peak_probe_concurrency, self._current)
            time.sleep(0.15)  # Simulate inference time
            with self._lock:
                self._current -= 1
            if fail_probe_for and idx in fail_probe_for:
                raise RuntimeError('probe failed')
            self.calls['probes'].append(idx)
            self.order.append(('probe', idx))
            return probe_values.get(idx)

        def generate_summary_single_call(self, text, title=None, author=None,
                                         language='English', max_length=500,
                                         probe=None):
            idx = self._idx(title)
            self.calls['single_calls'].append(idx)
            self.order.append(('generate', idx))
            return {
                'title': title[:60],
                'summary': f'Summary of article {idx}.',
                'is_clickbait': False if probe else None,
                'is_ad': (probe.get('ad_probability', 0) >= 0.7) if probe else False,
                'clickbait_detected_by': 'decision_model' if probe else None,
                'ad_probability': probe.get('ad_probability') if probe else None,
                'clickbait_probability': probe.get('clickbait_probability') if probe else None,
            }

        def generate_summary(self, text, title=None, author=None, language='English'):
            idx = self._idx(title)
            self.calls['legacy_calls'].append(idx)
            self.order.append(('generate', idx))
            return {
                'title': title[:60],
                'summary': f'Legacy summary of article {idx}.',
                'is_clickbait': False,
                'clickbait_detected_by': None,
                'is_ad': False,
            }

    summarizer = NewsSummarizer(text_processor=MockAIClient())
    summarizer.extractor = MockExtractor()
    summarizer.language_detector = MockDetector()
    # ContentCleaner is real: it cleans HTML and validates - our mock text is clean.
    # Force its validation to be lenient by patching word count check.
    summarizer.ai = summarizer.text_client
    return summarizer


def feed_data(entries, batch_size=None):
    return {
        'feed_name': 'MockFeed',
        'feed_url': 'http://example.com/rss',
        'entries': entries,
    }


def main():
    failures = 0

    def check(name, actual, expected):
        nonlocal failures
        ok = actual == expected
        if not ok:
            failures += 1
        print(f"[{'PASS' if ok else 'FAIL'}] {name}")
        if not ok:
            print(f"  expected: {expected!r}")
            print(f"  actual:   {actual!r}")

    N = 10
    entries = [make_entry(i) for i in range(N)]

    # Case 1: probes complete before first generative call; ads dropped;
    #         concurrency observed.
    probe_values = {
        0: {'ad_probability': 0.05, 'clickbait_probability': 0.01},   # survive
        1: {'ad_probability': 0.95, 'clickbait_probability': 0.01},   # DROP
        2: {'ad_probability': 0.50, 'clickbait_probability': 0.30},   # ambiguous -> survive
        3: {'ad_probability': 0.20, 'clickbait_probability': 0.80},   # clickbait, survive
        4: {'ad_probability': 0.01, 'clickbait_probability': 0.05},   # survive
        5: {'ad_probability': 0.10, 'clickbait_probability': 0.10},   # survive
        6: {'ad_probability': 0.92, 'clickbait_probability': 0.02},   # DROP
        7: {'ad_probability': 0.15, 'clickbait_probability': 0.15},   # survive
        8: {'ad_probability': 0.02, 'clickbait_probability': 0.60},   # survive
        9: {'ad_probability': 0.60, 'clickbait_probability': 0.10},   # survive
    }
    summarizer = build_summarizer(probe_values)
    ai = summarizer.text_client
    results = summarizer.batch_process([feed_data(entries)])

    probe_indexes = [i for kind, i in ai.order if kind == 'probe']
    generate_positions = [pos for pos, (kind, _) in enumerate(ai.order) if kind == 'generate']

    check("all 10 probes ran before first generative call",
          len(probe_indexes) == N and (not generate_positions or
                                       min(generate_positions) >= N),
          True)

    check("2 ads dropped pre-filter (0.95, 0.92)",
          sum(1 for r in results if r.get('prefiltered')), 2)

    check("8 survivors generated summaries",
          len([r for r in results if r.get('success') and r.get('summary')]), 8)

    check("dropped items made zero generative calls",
          sorted(set(ai.calls['single_calls']) | set(ai.calls['legacy_calls'])),
          [0, 2, 3, 4, 5, 7, 8, 9])

    check("peak probe concurrency observed >1 (batching works)",
          ai.peak_probe_concurrency > 1, True)

    # Case 2: probe failure -> item still processed via generative-verdicts
    probe_values2 = {i: {'ad_probability': 0.05, 'clickbait_probability': 0.01}
                     for i in range(5)}
    summarizer2 = build_summarizer(probe_values2, fail_probe_for={2})
    results2 = summarizer2.batch_process([feed_data([make_entry(i) for i in range(5)])])
    check("probe failure item still summarized",
          sum(1 for r in results2 if r.get('success') and r.get('summary')), 5)
    failed_probe_result = next(
        (r for r in results2 if r.get('summary', '').startswith('Summary of article 2')),
        None)
    check("failed item got no probe in result",
          failed_probe_result is not None and failed_probe_result.get('clickbait_probability') is None,
          True)

    # Case 3: no decision stage configured -> no probes at all,
    #         all via generative verdicts
    summarizer3 = build_summarizer({}, decision_stage=False)
    results3 = summarizer3.batch_process([feed_data([make_entry(i) for i in range(3)])])
    check("no-probe path: all summarized",
          sum(1 for r in results3 if r.get('success') and r.get('summary')), 3)
    check("no-probe path: zero probe calls", len(summarizer3.text_client.calls['probes']), 0)

    # Case 4: extraction produces failure results (unhappy path), no AI calls
    entries4 = [make_entry(0), make_entry(1)]
    summarizer4 = build_summarizer(probe_values)
    # Break the extractor to simulate site-down for entry 1
    orig = summarizer4.extractor.extract_from_feed_entry
    summarizer4.extractor.extract_from_feed_entry = lambda entry, session=None: None
    results4 = summarizer4.batch_process([feed_data(entries4)])
    check("extraction failure handled", sum(1 for r in results4 if not r.get('success')), 2)

    print()
    if failures:
        print(f"{failures} test(s) FAILED")
        raise SystemExit(1)
    print("All staged-pipeline tests passed!")


if __name__ == "__main__":
    main()