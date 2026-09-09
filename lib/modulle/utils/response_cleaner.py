"""
Utilities for cleaning LLM responses.

Thinking models (Qwen3, Qwen3.8, DeepSeek-R1, GLM, Nemotron, etc.) often emit
chain-of-thought reasoning either inside explicit tags or as plain text. This
module strips reasoning traces so applications receive only the final answer.
"""
import re
from typing import Optional

# Closed thinking blocks: <think>...</think> (Qwen3, DeepSeek-R1, GLM)
_THINK_BLOCK_RE = re.compile(
    r"<think>.*?</think>",
    re.DOTALL | re.IGNORECASE,
)

# Unclosed thinking block: <think> with no closing tag
_THINK_OPEN_RE = re.compile(
    r"<think>.*",
    re.DOTALL | re.IGNORECASE,
)

# Common chain-of-thought openers seen on Qwen3.8 / Nemotron family models
# when tags are missing entirely (e.g. "We need answer user: ...")
_REASONING_START_RE = re.compile(
    r"^(?:we need (?:to )?(?:answer|respond|generate|summarize|analyze|determine)|"
    r"okay,?(?: let'?s| so)?|let'?s (?:think|analyze|break|see)|"
    r"first,?(?: let'?s| i)?)\b",
    re.IGNORECASE,
)


def strip_think_tags(text: Optional[str]) -> str:
    """
    Remove thinking blocks (closed and unclosed) from a response.

    Args:
        text: Raw model response

    Returns:
        Text with thinking blocks removed
    """
    if not text:
        return ""
    cleaned = _THINK_BLOCK_RE.sub("", text)
    cleaned = _THINK_OPEN_RE.sub("", cleaned)
    return cleaned


def looks_like_reasoning(text: str) -> bool:
    """
    Heuristic check for untagged chain-of-thought reasoning.

    Args:
        text: Response text (should already have think tags stripped)

    Returns:
        True if the text starts with a known reasoning opener
    """
    if not text:
        return False
    return bool(_REASONING_START_RE.match(text.strip()))


def clean_response(text: Optional[str]) -> Optional[str]:
    """
    Clean a raw LLM response, stripping reasoning traces.

    Handles:
    - <think>...</think> blocks (tagged thinking models)
    - Unclosed <think> blocks (truncated/malformed output)
    - Leading plain-text reasoning ("We need answer...", "Let's think...")
      followed by a separated final answer

    Returns None when the response is empty or is pure unrecoverable
    reasoning, so callers can skip the item instead of publishing garbage.

    Args:
        text: Raw model response

    Returns:
        Cleaned response text, or None if nothing usable remains
    """
    if not text:
        return None

    cleaned = strip_think_tags(text).strip()
    if not cleaned:
        return None

    if looks_like_reasoning(cleaned):
        # Reasoning-first responses: the final answer usually follows a
        # paragraph break after the reasoning block. Try to salvage the
        # tail; if it is the only paragraph, it is unrecoverable.
        paragraphs = [p.strip() for p in cleaned.split("\n\n") if p.strip()]
        if len(paragraphs) > 1:
            tail = "\n\n".join(paragraphs[1:]).strip()
            if tail and not looks_like_reasoning(tail):
                return tail
        return None

    return cleaned


def parse_yes_no(text: Optional[str]) -> Optional[bool]:
    """
    Parse a yes/no classification from a model response.

    Only accepts responses whose final answer is a clear yes/no token,
    ignoring reasoning text that may mention 'yes' or 'no' in passing.

    Args:
        text: Raw model response

    Returns:
        True for 'yes', False for 'no', None if the answer is unclear
    """
    cleaned = clean_response(text)
    if not cleaned:
        return None

    normalized = cleaned.strip().strip("\"'`*.").lower()

    # Exact single-token answer (ideal case)
    if normalized in ("yes", "y", "true") :
        return True
    if normalized in ("no", "n", "false"):
        return False

    # Fallback: find a lone yes/no token among short noise (e.g. quoting
    # the question). A token adjacent to reasoning sentences is rejected.
    tokens = re.findall(r"\b(yes|no)\b", normalized)
    if len(tokens) == 1 and len(normalized) <= 40:
        return tokens[0] == "yes"

    return None