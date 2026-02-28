#!/usr/bin/env python3
"""
Quick test script for LM Studio integration.
Tests connectivity, model listing, and basic text generation.

Uses the factory pattern to create AI client.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import src.config as config_module
config_module.AI_PROVIDER = 'lm_studio'

from src.ai_client import create_ai_client_with_fallback
from src.config import LM_STUDIO_BASE_URL, LM_STUDIO_TEXT_MODEL


def main():
    """Run LM Studio integration test."""
    print("\n" + "="*60)
    print("LM STUDIO INTEGRATION TEST")
    print("="*60)
    print(f"Server: {LM_STUDIO_BASE_URL}")
    print(f"Model: {LM_STUDIO_TEXT_MODEL}")

    # Create client via factory
    print("\nCreating AI client...")
    try:
        ai_client, text_processor, vision_processor = create_ai_client_with_fallback()
    except Exception as e:
        print(f"ERROR: Failed to create AI client: {e}")
        return 1

    # Health check
    print(f"\n{'='*60}")
    print("Testing Health Check")
    print(f"{'='*60}")
    if ai_client.health_check():
        print("PASS: LM Studio server is accessible")
    else:
        print("FAIL: LM Studio server is not accessible")
        return 1

    # List models
    print(f"\n{'='*60}")
    print("Testing Model Listing")
    print(f"{'='*60}")
    models = ai_client.list_models()
    if models:
        print(f"PASS: Found {len(models)} model(s):")
        for model in models:
            print(f"  - {model}")
    else:
        print("FAIL: No models found")

    # Summarization test
    print(f"\n{'='*60}")
    print("Testing Article Summarization")
    print(f"{'='*60}")

    sample_text = (
        "Artificial intelligence (AI) is transforming the technology industry. "
        "Companies are investing billions in AI research and development. "
        "Machine learning models are becoming more sophisticated and capable. "
        "The impact on various sectors including healthcare, finance, and transportation is significant."
    )

    result = text_processor.generate_summary(
        text=sample_text,
        title="AI Industry Investment",
        author="Test Author"
    )

    if result:
        print(f"PASS: Generated Title: {result.get('title', 'N/A')}")
        print(f"PASS: Generated Summary: {result.get('summary', 'N/A')[:200]}...")
        print(f"Clickbait: {result.get('is_clickbait', False)}")
        print(f"Ad: {result.get('is_ad', False)}")
    else:
        print("FAIL: Failed to generate summary")
        return 1

    print(f"\n{'='*60}")
    print("All tests passed!")
    print(f"{'='*60}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
