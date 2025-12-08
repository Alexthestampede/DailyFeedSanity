#!/usr/bin/env python3
"""
Quick test to verify manual feed type override functionality
"""
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from feed_processor.feed_classifier import FeedClassifier
from config import FEED_TYPE_OVERRIDES_FILE


def test_manual_override():
    """Test that manual overrides work correctly"""

    print("Testing Manual Feed Type Override Mechanism")
    print("=" * 60)

    # Test feed URL
    test_url = "https://example.com/test-feed"

    # Initialize classifier
    classifier = FeedClassifier(use_ollama_detection=False)

    # Test 1: Without override (should default to 'comic')
    print("\n1. Testing without override:")
    result = classifier.classify_feed(test_url)
    print(f"   Result: {result}")
    assert result == 'comic', f"Expected 'comic', got '{result}'"
    print("   ✓ Correctly defaults to 'comic'")

    # Test 2: Create override file
    print("\n2. Creating override file with test entry:")
    override_content = f"""# Test override file
{test_url} = news
"""
    with open(FEED_TYPE_OVERRIDES_FILE, 'w') as f:
        f.write(override_content)
    print(f"   Created {FEED_TYPE_OVERRIDES_FILE}")

    # Test 3: With override (should return 'news')
    print("\n3. Testing with override:")
    classifier = FeedClassifier(use_ollama_detection=False)  # Reload to pick up new overrides
    result = classifier.classify_feed(test_url)
    print(f"   Result: {result}")
    assert result == 'news', f"Expected 'news' (from override), got '{result}'"
    print("   ✓ Override successfully applied!")

    # Test 4: Verify override takes priority over hardcoded config
    print("\n4. Testing priority (override vs hardcoded):")
    hardcoded_url = "https://questionablecontent.net/QCRSS.xml"
    override_content = f"""# Test override file
{hardcoded_url} = news
"""
    with open(FEED_TYPE_OVERRIDES_FILE, 'w') as f:
        f.write(override_content)

    classifier = FeedClassifier(use_ollama_detection=False)
    result = classifier.classify_feed(hardcoded_url)
    print(f"   URL: {hardcoded_url}")
    print(f"   Hardcoded type: comic")
    print(f"   Override type: news")
    print(f"   Result: {result}")
    assert result == 'news', f"Expected 'news' (override should win), got '{result}'"
    print("   ✓ Override correctly takes priority over hardcoded config!")

    # Clean up
    print("\n5. Cleaning up test file:")
    if os.path.exists(FEED_TYPE_OVERRIDES_FILE):
        os.remove(FEED_TYPE_OVERRIDES_FILE)
        print(f"   Removed {FEED_TYPE_OVERRIDES_FILE}")

    print("\n" + "=" * 60)
    print("All tests passed! ✓")
    print("\nManual override mechanism working correctly:")
    print("  1. Overrides load from feed_type_overrides.txt")
    print("  2. Overrides have highest priority")
    print("  3. System gracefully handles missing override file")


if __name__ == '__main__':
    try:
        test_manual_override()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
