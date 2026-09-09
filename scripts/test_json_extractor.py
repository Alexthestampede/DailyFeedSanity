#!/usr/bin/env python3
"""
Tests for json_extractor with realistic LLM response patterns.

Covers: bare JSON, fenced JSON, chatty preambles, reasoning traces
before/after JSON, malformed attempts, and the single-call workflow.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.modulle.utils.json_extractor import extract_json
from src.ai_client.domain_text_processor import DomainTextProcessor

THINK_OPEN = "<" + "think" + ">"
THINK_CLOSE = "<" + "/" + "think" + ">"

GOOD_JSON = {
    "title": "Dynamic Island Now Shows Three Live Activities",
    "summary": "Apple updated the iPhone 18 Pro Dynamic Island to display "
               "up to three Live Activities simultaneously.",
    "is_clickbait": False,
    "is_ad": False,
}


def main():
    failures = 0

    def check(name, actual, expected):
        nonlocal failures
        status = "PASS" if actual == expected else "FAIL"
        if actual != expected:
            failures += 1
        print(f"[{status}] {name}")
        if actual != expected and expected is not None:
            print(f"  expected: {expected!r}")
            print(f"  actual:   {actual!r}")

    import json
    expected = GOOD_JSON

    # 1. Bare JSON (ideal case)
    check("bare JSON", extract_json(json.dumps(GOOD_JSON)), expected)

    # 2. Fenced JSON
    check("fenced ```json block", extract_json(
        "```json\n" + json.dumps(GOOD_JSON) + "\n```"), expected)

    # 3. Chatty preamble + trailing commentary
    check("preamble + trailing chatter", extract_json(
        "Here is the JSON you requested:\n" + json.dumps(GOOD_JSON)
        + "\n\nHope this helps! Let me know if you need changes."), expected)

    # 4. Reasoning traces before/after (tagged)
    check("tagged reasoning + JSON", extract_json(
        THINK_OPEN + "Need to produce JSON with title, summary, verdicts."
        + THINK_CLOSE
        + json.dumps(GOOD_JSON)), expected)

    # 5. thehorror-style untagged reasoning + JSON
    check("untagged reasoning + JSON", extract_json(
        "We need answer user's request in English. Need produce JSON object "
        "with required fields.\n\n" + json.dumps(GOOD_JSON)), expected)

    # 6. JSON with braces inside string values
    tricky = {
        "title": "Apple {announces} new stuff",
        "summary": "Apple said: { \"quote\": \"nested braces in string\" } and more.",
        "is_clickbait": False,
        "is_ad": False,
    }
    check("braces inside strings", extract_json(json.dumps(tricky)), tricky)

    # 7. No JSON at all
    check("no JSON -> None", extract_json("I cannot comply with that request."), None)
    check("empty -> None", extract_json(""), None)
    check("None -> None", extract_json(None), None)

    # 8. Malformed JSON followed by valid one
    check("malformed then valid", extract_json(
        "{broken json\n" + json.dumps(GOOD_JSON)), expected)

    # 9. JSON with yes/no string verdicts (models that don't use booleans)
    str_verdicts = {
        "title": "Some headline here",
        "summary": "Something happened in tech news today.",
        "is_clickbait": "no",
        "is_ad": "yes",
    }
    parsed = extract_json(json.dumps(str_verdicts))
    check("string verdicts parsed", parsed, str_verdicts)

    # 10. Integration: single-call workflow with mocked model
    class MockSingleCall:
        def generate(self, prompt, system_prompt=None, temperature=0.7, max_tokens=None):
            return json.dumps(GOOD_JSON)

    proc = DomainTextProcessor(MockSingleCall(), enable_ad_detection=True)
    result = proc.generate_summary_single_call(
        "Some article text about Apple.", title="Original Title")
    check("single-call: full result", result, {
        "summary": GOOD_JSON["summary"],
        "title": GOOD_JSON["title"],
        "is_clickbait": False,
        "clickbait_detected_by": None,
        "is_ad": False,
    })

    # 11. Author clickbait overrides AI verdict False
    proc = DomainTextProcessor(MockSingleCall(), enable_ad_detection=True)
    result = proc.generate_summary_single_call(
        "Some article text.", title="T", author="Francesca Testa")
    check("author clickbait flag", (
        result["is_clickbait"] is True and result["clickbait_detected_by"] == "author"
    ), True)

    # 12. Ad detection disabled -> is_ad forced False even if model says true
    mock_says_ad = dict(GOOD_JSON, is_ad=True)

    class MockAdSaysTrue:
        def generate(self, prompt, system_prompt=None, temperature=0.7, max_tokens=None):
            return json.dumps(mock_says_ad)

    proc = DomainTextProcessor(MockAdSaysTrue(), enable_ad_detection=False)
    result = proc.generate_summary_single_call("Text.", title="T")
    check("ad toggle disabled forces is_ad=False", result["is_ad"], False)

    # 13. Reasoning leaked into summary field -> rejected
    bad_summary = dict(GOOD_JSON, summary="We need to answer the user's request properly.")

    class MockLeakySummary:
        def generate(self, prompt, system_prompt=None, temperature=0.7, max_tokens=None):
            return json.dumps(bad_summary)

    proc = DomainTextProcessor(MockLeakySummary(), enable_ad_detection=True)
    check("reasoning in summary field -> None",
          proc.generate_summary_single_call("Text.", title="T"), None)

    # 14. No JSON in response -> None
    class MockNoJSON:
        def generate(self, prompt, system_prompt=None, temperature=0.7, max_tokens=None):
            return "The user wants me to create a JSON object. Let me do that now."

    proc = DomainTextProcessor(MockNoJSON(), enable_ad_detection=True)
    check("pure chatter response -> None",
          proc.generate_summary_single_call("Text.", title="T"), None)

    print()
    if failures:
        print(f"{failures} test(s) FAILED")
        raise SystemExit(1)
    print("All JSON extractor tests passed!")


if __name__ == "__main__":
    main()