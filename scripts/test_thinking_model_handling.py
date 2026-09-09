#!/usr/bin/env python3
"""
Integration test: DomainTextProcessor with a mocked thinking model.

Simulates Qwen 3.8 27B behavior from logs/thehorror.html:
- Untagged chain-of-thought in summaries
- Prompt echoes in titles
- Reasoning-contaminated yes/no detection responses
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ai_client.domain_text_processor import DomainTextProcessor

THINK_OPEN = "<" + "think" + ">"
THINK_CLOSE = "<" + "/" + "think" + ">"


class MockThinkingProcessor:
    """Returns thinking-model style garbage like thehorror.html showed."""

    def __init__(self, mode):
        self.mode = mode
        self.calls = 0

    def generate(self, prompt, system_prompt=None, temperature=0.7, max_tokens=None):
        self.calls += 1
        if self.mode == "untagged_pure":
            # The thehorror pattern: pure reasoning, no answer
            return (
                "We need answer in English. User asks summarize article, "
                "objective factual summary strips sensationalism, neutral "
                "skeptical tone. Article: Apple updated the Dynamic Island."
            )
        if self.mode == "reasoning_then_answer":
            return (
                "We need answer user: \"Generate a headline\"\n\n"
                "Dynamic Island Now Shows Three Live Activities"
            )
        if self.mode == "detection_garbage":
            # thehorror failure mode: reasoning that mentions 'yes' in passing
            return (
                "We need analyze if this is clickbait. The title says "
                "'you won't believe' but the answer is no, content is factual."
            )
        if self.mode == "tagged_thinking":
            return (
                THINK_OPEN + "Let me think. Need summarize article."
                + THINK_CLOSE
                + "Apple updated the Dynamic Island to show three Live Activities."
            )
        return "Clean response."


def main():
    results = []

    # 1. Pure untagged reasoning summary -> generate_summary returns None
    mock = MockThinkingProcessor("untagged_pure")
    proc = DomainTextProcessor(mock)
    result = proc.generate_summary("Some article text.", title="Title")
    results.append(("pure reasoning summary rejected", result is None))

    # 2. Reasoning-then-answer summary -> salvaged answer
    mock = MockThinkingProcessor("reasoning_then_answer")
    proc = DomainTextProcessor(mock)
    result = proc.generate_summary("Some article text.", title="Title")
    results.append((
        "reasoning+answer summary salvaged",
        result is not None and "We need" not in result["summary"],
    ))

    # 3. Detection with garbage reasoning response -> NOT flagged as clickbait
    mock = MockThinkingProcessor("detection_garbage")
    proc = DomainTextProcessor(mock)
    is_clickbait = proc.detect_clickbait("Some Title", "Some article text.")
    results.append(("contaminated detection -> False (not True)", is_clickbait is False))

    # 4. Detection with garbage response -> NOT flagged as ad
    is_ad = proc.detect_ad("Some Title", "Some article text.")
    results.append(("contaminated ad detection -> False (not True)", is_ad is False))

    # 5. Tagged thinking summary -> clean answer
    mock = MockThinkingProcessor("tagged_thinking")
    proc = DomainTextProcessor(mock)
    result = proc.generate_summary("Some article text.", title="Title")
    results.append((
        "tagged thinking -> clean summary",
        result is not None and "Let me think" not in result["summary"],
    ))

    print()
    failures = 0
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        if not passed:
            failures += 1
        print(f"[{status}] {name}")

    print()
    if failures:
        print(f"{failures} test(s) FAILED")
        raise SystemExit(1)
    print("All integration tests passed!")


if __name__ == "__main__":
    main()