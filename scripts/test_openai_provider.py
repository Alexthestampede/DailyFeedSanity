#!/usr/bin/env python3
"""
Test script for OpenAI provider integration.

This script tests the OpenAI provider's text and vision capabilities
without running the full RSS processor.

Usage:
    # Test text summarization
    python scripts/test_openai_provider.py --test text

    # Test vision processing
    python scripts/test_openai_provider.py --test vision

    # Test health check
    python scripts/test_openai_provider.py --test health

    # Test all
    python scripts/test_openai_provider.py --test all

Requirements:
    - OPENAI_API_KEY environment variable must be set
    - For vision tests, provide an image path with --image flag
"""

import argparse
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.openai_provider import OpenAIClient, OpenAITextProcessor, OpenAIVisionProcessor
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def test_health_check():
    """Test OpenAI API health check."""
    print("\n" + "="*60)
    print("Testing OpenAI API Health Check")
    print("="*60)

    try:
        client = OpenAIClient()
        is_healthy = client.health_check()

        if is_healthy:
            print("✓ OpenAI API is accessible")
            return True
        else:
            print("✗ OpenAI API is not accessible")
            return False

    except ValueError as e:
        print(f"✗ Error: {e}")
        return False


def test_list_models():
    """Test listing OpenAI models."""
    print("\n" + "="*60)
    print("Testing Model Listing")
    print("="*60)

    try:
        client = OpenAIClient()
        models = client.list_models()

        if models:
            print(f"✓ Retrieved {len(models)} models")
            print("\nSome available models:")
            # Show GPT models only
            gpt_models = [m for m in models if 'gpt' in m.lower()][:10]
            for model in gpt_models:
                print(f"  - {model}")
            return True
        else:
            print("✗ No models retrieved")
            return False

    except ValueError as e:
        print(f"✗ Error: {e}")
        return False


def test_text_summarization():
    """Test text summarization."""
    print("\n" + "="*60)
    print("Testing Text Summarization")
    print("="*60)

    # Sample article text
    article = {
        'text': """
        Artificial intelligence has made remarkable progress in recent years,
        particularly in the field of natural language processing. Large language
        models like GPT-4 can now understand and generate human-like text with
        unprecedented accuracy. These models are being used in various applications,
        from chatbots to content creation, translation, and code generation.
        However, challenges remain in areas such as reasoning, factual accuracy,
        and avoiding biases present in training data.
        """,
        'title': 'Advances in AI Language Models',
        'author': 'Tech Reporter',
        'url': 'https://example.com/ai-article'
    }

    try:
        processor = OpenAITextProcessor(model="gpt-4o-mini")
        print(f"Using model: gpt-4o-mini")

        print("\nSummarizing article...")
        result = processor.summarize_article(article)

        if result:
            print("\n✓ Summary generated successfully:")
            print(f"\nGenerated Title: {result['title']}")
            print(f"\nSummary:\n{result['summary']}")
            print(f"\nClickbait detected: {result['is_clickbait']}")
            if result['clickbait_detected_by']:
                print(f"Detection method: {result['clickbait_detected_by']}")
            return True
        else:
            print("✗ Failed to generate summary")
            return False

    except ValueError as e:
        print(f"✗ Error: {e}")
        return False


def test_clickbait_detection():
    """Test clickbait detection."""
    print("\n" + "="*60)
    print("Testing Clickbait Detection")
    print("="*60)

    # Test cases
    test_cases = [
        {
            'title': "You Won't Believe What This AI Can Do!",
            'text': "This amazing AI will shock you with its capabilities...",
            'expected': True
        },
        {
            'title': "New Study Reveals Effects of Climate Change",
            'text': "Scientists have published findings on climate patterns...",
            'expected': False
        }
    ]

    try:
        processor = OpenAITextProcessor(model="gpt-4o-mini")

        results = []
        for i, case in enumerate(test_cases, 1):
            print(f"\nTest {i}: {case['title']}")
            is_clickbait = processor.detect_clickbait(case['title'], case['text'])
            print(f"  Detected as clickbait: {is_clickbait}")
            print(f"  Expected: {case['expected']}")

            if is_clickbait == case['expected']:
                print("  ✓ Correct")
                results.append(True)
            else:
                print("  ⚠ Unexpected result")
                results.append(False)

        success_rate = sum(results) / len(results) * 100
        print(f"\nSuccess rate: {success_rate:.0f}%")
        return success_rate >= 50  # At least 50% correct

    except ValueError as e:
        print(f"✗ Error: {e}")
        return False


def test_vision_processing(image_path=None):
    """Test vision processing."""
    print("\n" + "="*60)
    print("Testing Vision Processing")
    print("="*60)

    if not image_path:
        print("⚠ No image path provided, skipping vision test")
        print("  Use --image flag to provide an image path")
        return None

    if not os.path.exists(image_path):
        print(f"✗ Image not found: {image_path}")
        return False

    try:
        processor = OpenAIVisionProcessor(model="gpt-4o")
        print(f"Using model: gpt-4o")
        print(f"Analyzing image: {image_path}")

        result = processor.analyze_image(
            image_path,
            "Describe this image in detail."
        )

        if result:
            print("\n✓ Vision analysis successful:")
            print(f"\n{result}")
            return True
        else:
            print("✗ Failed to analyze image")
            return False

    except ValueError as e:
        print(f"✗ Error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Test OpenAI provider integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--test',
        choices=['health', 'models', 'text', 'clickbait', 'vision', 'all'],
        default='all',
        help='Which test to run (default: all)'
    )
    parser.add_argument(
        '--image',
        help='Path to image file for vision testing'
    )

    args = parser.parse_args()

    # Check for API key
    if not os.getenv('OPENAI_API_KEY'):
        print("\n" + "="*60)
        print("ERROR: OPENAI_API_KEY environment variable not set")
        print("="*60)
        print("\nPlease set your OpenAI API key:")
        print("  export OPENAI_API_KEY='sk-your-key-here'")
        print("\nGet your API key from: https://platform.openai.com/api-keys")
        return 1

    results = {}

    if args.test in ['health', 'all']:
        results['health'] = test_health_check()

    if args.test in ['models', 'all']:
        results['models'] = test_list_models()

    if args.test in ['text', 'all']:
        results['text'] = test_text_summarization()

    if args.test in ['clickbait', 'all']:
        results['clickbait'] = test_clickbait_detection()

    if args.test in ['vision', 'all']:
        results['vision'] = test_vision_processing(args.image)

    # Print summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)

    for test_name, result in results.items():
        if result is None:
            status = "SKIPPED"
            symbol = "⊘"
        elif result:
            status = "PASSED"
            symbol = "✓"
        else:
            status = "FAILED"
            symbol = "✗"

        print(f"{symbol} {test_name.capitalize()}: {status}")

    # Overall result
    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    skipped = sum(1 for r in results.values() if r is None)

    print(f"\nTotal: {passed} passed, {failed} failed, {skipped} skipped")

    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
