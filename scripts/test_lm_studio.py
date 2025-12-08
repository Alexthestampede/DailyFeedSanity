#!/usr/bin/env python3
"""
Quick test script for LM Studio integration.
Tests connectivity, model listing, and basic text generation.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.lm_studio_client.client import LMStudioClient
from src.lm_studio_client.text_processor import LMStudioTextClient
from src.config import LM_STUDIO_BASE_URL, LM_STUDIO_TEXT_MODEL


def test_health_check():
    """Test LM Studio server connectivity."""
    print(f"\n{'='*60}")
    print("Testing LM Studio Health Check")
    print(f"{'='*60}")

    client = LMStudioClient(base_url=LM_STUDIO_BASE_URL)

    if client.health_check():
        print("✓ LM Studio server is accessible")
        return True
    else:
        print("✗ LM Studio server is not accessible")
        return False


def test_list_models():
    """Test listing available models."""
    print(f"\n{'='*60}")
    print("Testing Model Listing")
    print(f"{'='*60}")

    client = LMStudioClient(base_url=LM_STUDIO_BASE_URL)
    models = client.list_models()

    if models:
        print(f"✓ Found {len(models)} model(s):")
        for model in models:
            print(f"  - {model}")
        return True
    else:
        print("✗ No models found or error occurred")
        return False


def test_text_generation():
    """Test basic text generation."""
    print(f"\n{'='*60}")
    print("Testing Text Generation")
    print(f"{'='*60}")

    client = LMStudioClient(base_url=LM_STUDIO_BASE_URL)

    test_prompt = "What is the capital of France? Answer in one word."
    print(f"Prompt: {test_prompt}")
    print(f"Using model: {LM_STUDIO_TEXT_MODEL}")

    response = client.generate(
        prompt=test_prompt,
        system="You are a helpful assistant. Be concise.",
        temperature=0.1,
        model=LM_STUDIO_TEXT_MODEL
    )

    if response:
        print(f"✓ Response: {response}")
        return True
    else:
        print("✗ Failed to generate response")
        return False


def test_summarization():
    """Test article summarization."""
    print(f"\n{'='*60}")
    print("Testing Article Summarization")
    print(f"{'='*60}")

    text_processor = LMStudioTextClient(model=LM_STUDIO_TEXT_MODEL)

    sample_text = """
    Artificial intelligence (AI) is transforming the technology industry.
    Companies are investing billions in AI research and development.
    Machine learning models are becoming more sophisticated and capable.
    The impact on various sectors including healthcare, finance, and transportation is significant.
    """

    print("Sample text:")
    print(sample_text.strip())
    print("\nGenerating summary...")

    result = text_processor.generate_summary(
        text=sample_text,
        title="AI Industry Investment",
        author="Test Author"
    )

    if result:
        print(f"\n✓ Generated Title: {result.get('title', 'N/A')}")
        print(f"✓ Generated Summary: {result.get('summary', 'N/A')}")
        print(f"✓ Clickbait Detected: {result.get('is_clickbait', False)}")
        if result.get('clickbait_detected_by'):
            print(f"  Detection method: {result.get('clickbait_detected_by')}")
        return True
    else:
        print("✗ Failed to generate summary")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("LM STUDIO INTEGRATION TEST")
    print("="*60)
    print(f"Server: {LM_STUDIO_BASE_URL}")
    print(f"Model: {LM_STUDIO_TEXT_MODEL}")

    tests = [
        ("Health Check", test_health_check),
        ("Model Listing", test_list_models),
        ("Text Generation", test_text_generation),
        ("Summarization", test_summarization),
    ]

    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n✗ Error in {name}: {e}")
            results.append((name, False))

    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")

    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {name}")

    passed = sum(1 for _, s in results if s)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ All tests passed! LM Studio integration is working correctly.")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed. Check configuration and server status.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
