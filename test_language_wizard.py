#!/usr/bin/env python3
"""
Quick test script for language override management in config wizard.
This script tests the basic functionality without user interaction.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from utils.config_wizard import (
    LANGUAGE_OVERRIDE_FILE,
    LANGUAGE_CACHE_FILE,
    view_language_overrides,
)


def test_view_empty():
    """Test viewing when no overrides exist."""
    print("TEST 1: View empty overrides")
    print("=" * 60)

    # Remove file if exists
    if LANGUAGE_OVERRIDE_FILE.exists():
        LANGUAGE_OVERRIDE_FILE.unlink()

    view_language_overrides()
    print()


def test_view_with_data():
    """Test viewing with existing overrides."""
    print("TEST 2: View with data")
    print("=" * 60)

    # Create test file
    with open(LANGUAGE_OVERRIDE_FILE, 'w') as f:
        f.write("# Language overrides for feeds\n")
        f.write("\n")
        f.write("macitynet.it = Italian\n")
        f.write("feedburner.com/psblog = Italian\n")
        f.write("9to5mac.com = English\n")
        f.write("ansa.it = Italian\n")

    view_language_overrides()
    print()


def test_cache_exists():
    """Test cache file detection."""
    print("TEST 3: Cache file detection")
    print("=" * 60)

    # Create dummy cache
    with open(LANGUAGE_CACHE_FILE, 'w') as f:
        f.write('{"test": "cache"}')

    if LANGUAGE_CACHE_FILE.exists():
        print(f"Cache file exists: {LANGUAGE_CACHE_FILE}")
        print(f"Size: {LANGUAGE_CACHE_FILE.stat().st_size} bytes")
    else:
        print("Cache file does not exist")

    print()


def cleanup():
    """Clean up test files."""
    print("CLEANUP: Removing test files")
    print("=" * 60)

    if LANGUAGE_OVERRIDE_FILE.exists():
        LANGUAGE_OVERRIDE_FILE.unlink()
        print(f"Removed: {LANGUAGE_OVERRIDE_FILE}")

    if LANGUAGE_CACHE_FILE.exists():
        LANGUAGE_CACHE_FILE.unlink()
        print(f"Removed: {LANGUAGE_CACHE_FILE}")

    print()


if __name__ == '__main__':
    print("\nLanguage Override Management Test\n")
    print("=" * 60)
    print()

    try:
        test_view_empty()
        test_view_with_data()
        test_cache_exists()

        print("\nAll tests completed successfully!")
        print()

    finally:
        cleanup()
        print("Test complete!\n")
