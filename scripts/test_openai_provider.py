#!/usr/bin/env python3
"""
Test script for OpenAI provider integration.

Uses the factory pattern to create AI client with OpenAI provider.

Usage:
    # Test text summarization
    python scripts/test_openai_provider.py --test text

    # Test vision processing
    python scripts/test_openai_provider.py --test vision --image path/to/image.png

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

import src.config as config_module
config_module.AI_PROVIDER = 'openai'

from src.ai_client import create_ai_client_with_fallback
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def test_health_check(ai_client):
    """Test OpenAI API health check."""
    print("\n" + "="*60)
    print("Testing OpenAI API Health Check")
    print("="*60)

    try:
        is_healthy = ai_client.health_check()
        if is_healthy:
            print("PASS: OpenAI API is accessible")
            return True
        else:
            print("FAIL: OpenAI API is not accessible")
            return False
    except Exception as e:
        print(f"FAIL: {e}")
        return False


def test_list_models(ai_client):
    """Test listing OpenAI models."""
    print("\n" + "="*60)
    print("Testing Model Listing")
    print("="*60)

    try:
        models = ai_client.list_models()
        if models:
            print(f"PASS: Retrieved {len(models)} models")
            gpt_models = [m for m in models if 'gpt' in m.lower()][:10]
            if gpt_models:
                print("\nSome available GPT models:")
                for model in gpt_models:
                    print(f"  - {model}")
            return True
        else:
            print("FAIL: No models retrieved")
            return False
    except Exception as e:
        print(f"FAIL: {e}")
        return False


def test_text_summarization(text_processor):
    """Test text summarization."""
    print("\n" + "="*60)
    print("Testing Text Summarization")
    print("="*60)

    sample_text = (
        "Artificial intelligence has made remarkable progress in recent years, "
        "particularly in the field of natural language processing. Large language "
        "models like GPT-4 can now understand and generate human-like text with "
        "unprecedented accuracy. These models are being used in various applications, "
        "from chatbots to content creation, translation, and code generation. "
        "However, challenges remain in areas such as reasoning, factual accuracy, "
        "and avoiding biases present in training data."
    )

    try:
        result = text_processor.generate_summary(
            text=sample_text,
            title="Advances in AI Language Models",
            author="Tech Reporter"
        )

        if result:
            print(f"PASS: Generated Title: {result.get('title', 'N/A')}")
            print(f"PASS: Generated Summary: {result.get('summary', 'N/A')[:200]}...")
            print(f"Clickbait: {result.get('is_clickbait', False)}")
            print(f"Ad: {result.get('is_ad', False)}")
            return True
        else:
            print("FAIL: Failed to generate summary")
            return False
    except Exception as e:
        print(f"FAIL: {e}")
        return False


def test_clickbait_detection(text_processor):
    """Test clickbait detection."""
    print("\n" + "="*60)
    print("Testing Clickbait Detection")
    print("="*60)

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
        results = []
        for i, case in enumerate(test_cases, 1):
            print(f"\nTest {i}: {case['title']}")
            is_clickbait = text_processor.detect_clickbait(case['title'], case['text'])
            print(f"  Detected as clickbait: {is_clickbait}")
            print(f"  Expected: {case['expected']}")

            if is_clickbait == case['expected']:
                print("  PASS")
                results.append(True)
            else:
                print("  WARN: Unexpected result")
                results.append(False)

        success_rate = sum(results) / len(results) * 100
        print(f"\nSuccess rate: {success_rate:.0f}%")
        return success_rate >= 50
    except Exception as e:
        print(f"FAIL: {e}")
        return False


def test_vision_processing(vision_processor, image_path=None):
    """Test vision processing."""
    print("\n" + "="*60)
    print("Testing Vision Processing")
    print("="*60)

    if not vision_processor:
        print("SKIP: No vision processor available")
        return None

    if not image_path:
        print("SKIP: No image path provided (use --image flag)")
        return None

    if not os.path.exists(image_path):
        print(f"FAIL: Image not found: {image_path}")
        return False

    try:
        encoded = vision_processor.encode_image_from_file(image_path)
        if not encoded:
            print("FAIL: Failed to encode image")
            return False

        result = vision_processor.processor.analyze_image(
            image_data=encoded,
            prompt="Describe this image in detail."
        )

        if result:
            print(f"\nPASS: Vision analysis successful:")
            print(f"\n{result}")
            return True
        else:
            print("FAIL: No response from vision model")
            return False
    except Exception as e:
        print(f"FAIL: {e}")
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

    # Create client via factory
    print("\nCreating OpenAI AI client...")
    try:
        ai_client, text_processor, vision_processor = create_ai_client_with_fallback()
    except Exception as e:
        print(f"ERROR: Failed to create AI client: {e}")
        return 1

    results = {}

    if args.test in ['health', 'all']:
        results['health'] = test_health_check(ai_client)

    if args.test in ['models', 'all']:
        results['models'] = test_list_models(ai_client)

    if args.test in ['text', 'all']:
        results['text'] = test_text_summarization(text_processor)

    if args.test in ['clickbait', 'all']:
        results['clickbait'] = test_clickbait_detection(text_processor)

    if args.test in ['vision', 'all']:
        results['vision'] = test_vision_processing(vision_processor, args.image)

    # Print summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)

    for test_name, result in results.items():
        if result is None:
            status = "SKIPPED"
        elif result:
            status = "PASSED"
        else:
            status = "FAILED"
        print(f"  {test_name.capitalize()}: {status}")

    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    skipped = sum(1 for r in results.values() if r is None)
    print(f"\nTotal: {passed} passed, {failed} failed, {skipped} skipped")

    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
