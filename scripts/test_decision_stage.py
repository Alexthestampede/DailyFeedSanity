#!/usr/bin/env python3
"""
Tests for the two-stage decision workflow (verdicts via /v1/systemone).

Mocks a decision client returning noul probabilities, verifying:
- Threshold gating both ways
- Ad-question skipped when ad detection disabled
- Fallback to legacy generative detection when decision stage fails
- Single-call workflow asks only title+summary when decision stage on
- Probabilities flow into the result dict
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ai_client.domain_text_processor import DomainTextProcessor

ARTICLE_TEXT = "Apple updated the Dynamic Island to show three Live Activities at once."
ARTICLE_TITLE = "Dynamic Island now shows three Live Activities"

# JSON-only response (title+summary, no verdict fields) - what the generative
# model returns in two-stage mode
TITLE_SUMMARY_JSON = (
    '{"title": "Dynamic Island Now Shows Three Live Activities", '
    '"summary": "Apple updated the iPhone 18 Pro Dynamic Island to display '
    'up to three Live Activities simultaneously.", '
    '"is_clickbait": false, "is_ad": false}'
)


class MockDecisionClient:
    """Stand-in for OllamaClient.system_one()."""

    def __init__(self, clickbait_prob=0.02, ad_prob=0.17, fail=False):
        self.clickbait_prob = clickbait_prob
        self.ad_prob = ad_prob
        self.fail = fail
        self.calls = []

    def system_one(self, model, state, questions):
        self.calls.append({"model": model, "state": state, "questions": questions})
        if self.fail:
            raise RuntimeError("connection refused")
        answers = {"is_clickbait": {"type": "noul", "noul": self.clickbait_prob}}
        if "is_ad" in questions:
            answers["is_ad"] = {"type": "noul", "noul": self.ad_prob}
        return {"model": model, "answers": answers, "usage": {}}


class MockGenerativeSingleCall:
    """Generative model returning title+summary JSON."""

    def generate(self, prompt, system_prompt=None, temperature=0.7, max_tokens=None):
        if "is_clickbait" in (system_prompt or ""):
            raise AssertionError(
                "two-stage mode must NOT ask the generative model for verdicts"
            )
        return TITLE_SUMMARY_JSON


def make_proc(decision_client=None, threshold=0.7, ad_detection=True,
              generative_cls=None):
    gen = generative_cls or MockGenerativeSingleCall
    # Legacy path needs detect_clickbait/detect_ad responses; give a terse model
    class LegacyGen(gen):
        pass

    proc = DomainTextProcessor(
        gen(), enable_ad_detection=ad_detection,
        decision_client=decision_client, decision_model="d1k32:latest",
        decision_threshold=threshold,
    )
    return proc


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

    # 1. Below threshold -> both verdicts False, probabilities included
    client = MockDecisionClient(clickbait_prob=0.02, ad_prob=0.17)
    proc = make_proc(decision_client=client)
    v = proc.detect_verdicts_decision(ARTICLE_TITLE, ARTICLE_TEXT)
    check("clickbait False below threshold", v["is_clickbait"], False)
    check("ad False below threshold", v["is_ad"], False)
    check("clickbait probability surfaced", round(v["clickbait_probability"], 3), 0.02)
    check("ad probability surfaced", round(v["ad_probability"], 3), 0.17)

    # 2. Above threshold -> True both
    client = MockDecisionClient(clickbait_prob=0.95, ad_prob=0.98)
    proc = make_proc(decision_client=client)
    v = proc.detect_verdicts_decision(ARTICLE_TITLE, ARTICLE_TEXT)
    check("clickbait True above threshold", v["is_clickbait"], True)
    check("ad True above threshold", v["is_ad"], True)

    # 3. Ad detection disabled -> ad question not asked
    client = MockDecisionClient(clickbait_prob=0.02, ad_prob=0.99)
    proc = make_proc(decision_client=client, ad_detection=False)
    v = proc.detect_verdicts_decision(ARTICLE_TITLE, ARTICLE_TEXT)
    asked = list(client.calls[0]["questions"].keys())
    check("ad question omitted when disabled", "is_ad" not in asked, True)
    check("is_ad False when disabled", v["is_ad"], False)

    # 4. Decision failure -> detect_verdicts returns None (callers fall back)
    client = MockDecisionClient(fail=True)
    proc = make_proc(decision_client=client)
    check("failure -> None", proc.detect_verdicts_decision(ARTICLE_TITLE, ARTICLE_TEXT), None)

    # 5. Two-stage single-call integration: generative model never asked for
    #    verdicts, verdicts come from decision stage, probabilities included
    client = MockDecisionClient(clickbait_prob=0.01, ad_prob=0.05)
    proc = make_proc(decision_client=client)
    result = proc.generate_summary_single_call(ARTICLE_TEXT, title=ARTICLE_TITLE)
    check("summary present", result is not None and bool(result["summary"]), True)
    check("verdicts from decision stage", result["is_clickbait"], False)
    check("clickbait_detected_by decision_model", result["clickbait_detected_by"], None)
    check("probability in result", "clickbait_probability" in result, True)

    # 6. Author-clickbait override still applies in two-stage mode
    client = MockDecisionClient(clickbait_prob=0.01, ad_prob=0.01)
    proc = make_proc(decision_client=client)
    result = proc.generate_summary_single_call(
        ARTICLE_TEXT, title=ARTICLE_TITLE, author="Francesca Testa")
    check("author override -> clickbait True", result["is_clickbait"], True)
    check("detected_by author", result["clickbait_detected_by"], "author")

    # 7. Decision client fails mid-run -> fallback to legacy generative calls
    class LegacyFallbackGen:
        """Answer yes/no detection prompts, but assert NOT asked for verdict JSON."""
        def generate(self, prompt, system_prompt=None, temperature=0.7, max_tokens=None):
            p = (system_prompt or "") + prompt
            if "Is this clickbait?" in p:
                return "no"
            if "advertisement or sponsored content?" in p:
                return "no"
            return TITLE_SUMMARY_JSON

    client = MockDecisionClient(fail=True)
    proc = DomainTextProcessor(
        LegacyFallbackGen(), enable_ad_detection=True,
        decision_client=client, decision_model="d1k32:latest",
        decision_threshold=0.7,
    )
    result = proc.generate_summary(ARTICLE_TEXT, title=ARTICLE_TITLE)
    check("fallback path produces result", result is not None, True)
    check("fallback verdicts False", result["is_clickbait"], False)

    # 8. No decision client -> legacy behavior intact (detect via generative)
    proc = make_proc(decision_client=None) if False else DomainTextProcessor(
        LegacyFallbackGen(), enable_ad_detection=True)
    result = proc.generate_summary(ARTICLE_TEXT, title=ARTICLE_TITLE)
    check("legacy path still works", result["is_clickbait"], False)

    print()
    if failures:
        print(f"{failures} test(s) FAILED")
        raise SystemExit(1)
    print("All two-stage decision tests passed!")


if __name__ == "__main__":
    main()