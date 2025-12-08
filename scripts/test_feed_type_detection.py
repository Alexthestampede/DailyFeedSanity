#!/usr/bin/env python3
"""
Test script for automatic feed type detection using Ollama.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.feed_processor.feed_parser import FeedParser
from src.feed_processor.feed_classifier import FeedClassifier
from src.utils.logging_config import setup_logging
from src.config import FEED_TYPES


def test_known_feed(feed_url):
    """Test classification of a known feed."""
    print(f"\n{'='*80}")
    print(f"Testing known feed: {feed_url}")
    print(f"{'='*80}")

    parser = FeedParser()
    classifier = FeedClassifier(use_ollama_detection=True)

    # Parse feed
    print("Parsing feed...")
    feed_data = parser.parse_feed(feed_url)

    if not feed_data:
        print("ERROR: Failed to parse feed")
        return

    print(f"Feed title: {feed_data.get('title', 'Unknown')}")
    print(f"Entries found: {len(feed_data.get('entries', []))}")

    # Show a few sample entries
    entries = feed_data.get('entries', [])[:3]
    print("\nSample entries:")
    for i, entry in enumerate(entries, 1):
        print(f"  {i}. {entry.get('title', 'Untitled')}")
        print(f"     URL: {entry.get('link', 'No URL')}")

    # Classify feed
    print("\nClassifying feed...")
    feed_type = classifier.classify_feed(feed_url, feed_data=feed_data)

    print(f"\nResult: {feed_type}")

    # Check if it's in known feeds
    domain = feed_url.split('/')[2].replace('www.', '')
    expected_type = None
    for known_domain, ftype in FEED_TYPES.items():
        if known_domain in domain:
            expected_type = ftype
            break

    if expected_type:
        if expected_type == feed_type:
            print(f"✓ Matches expected type: {expected_type}")
        else:
            print(f"✗ Expected: {expected_type}, Got: {feed_type}")
    else:
        print(f"(New feed - no expected type)")


def test_unknown_feed(feed_url):
    """Test classification of an unknown feed using Ollama."""
    print(f"\n{'='*80}")
    print(f"Testing UNKNOWN feed (will use Ollama): {feed_url}")
    print(f"{'='*80}")

    parser = FeedParser()
    classifier = FeedClassifier(use_ollama_detection=True)

    # Parse feed
    print("Parsing feed...")
    feed_data = parser.parse_feed(feed_url)

    if not feed_data:
        print("ERROR: Failed to parse feed")
        return

    print(f"Feed title: {feed_data.get('title', 'Unknown')}")
    print(f"Entries found: {len(feed_data.get('entries', []))}")

    # Show a few sample entries
    entries = feed_data.get('entries', [])[:5]
    print("\nSample entries (showing up to 5):")
    for i, entry in enumerate(entries, 1):
        title = entry.get('title', 'Untitled')
        link = entry.get('link', 'No URL')
        desc = entry.get('description', '')[:100]
        print(f"  {i}. {title}")
        print(f"     URL: {link}")
        if desc:
            print(f"     Desc: {desc}...")

    # Classify feed (this will use Ollama for unknown feeds)
    print("\nClassifying feed (using Ollama detection)...")
    feed_type = classifier.classify_feed(feed_url, feed_data=feed_data)

    print(f"\n{'='*40}")
    print(f"RESULT: {feed_type.upper()}")
    print(f"{'='*40}")


def main():
    """Main test function."""
    setup_logging(debug=True)

    if len(sys.argv) > 1:
        # Test specific feed from command line
        feed_url = sys.argv[1]
        test_unknown_feed(feed_url)
    else:
        # Test a few known feeds to verify the classification works
        print("\n" + "="*80)
        print("FEED TYPE DETECTION TEST SUITE")
        print("="*80)

        # Test a known comic feed
        print("\n1. Testing known COMIC feed (XKCD)...")
        test_known_feed("https://xkcd.com/rss.xml")

        # Test a known news feed
        print("\n2. Testing known NEWS feed (MacityNet)...")
        test_known_feed("https://feeds.feedburner.com/macitynet/MCNews")

        # Print summary
        print("\n" + "="*80)
        print("Tests complete!")
        print("="*80)
        print("\nTo test an unknown feed, run:")
        print("  python scripts/test_feed_type_detection.py <feed_url>")
        print("\nExample:")
        print("  python scripts/test_feed_type_detection.py https://example.com/feed.xml")


if __name__ == '__main__':
    main()
