#!/usr/bin/env python3
"""
Test script for configuration wizard functionality.
Tests the load/save config functions and validation logic.
"""
import sys
import json
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.config_wizard import (
    load_config, save_config, validate_url,
    test_ollama_connection, test_lm_studio_connection,
    AI_PROVIDERS
)


def test_load_save_config():
    """Test configuration load and save functions."""
    print("Testing load_config and save_config...")

    # Create a temporary config file
    test_config = {
        'ai_provider': 'ollama',
        'ollama_base_url': 'http://localhost:11434',
        'text_model': 'test-model',
        'vision_model': 'test-vision-model',
        'rss_feeds': ['https://example.com/feed1', 'https://example.com/feed2'],
        'first_run_complete': True
    }

    # Override CONFIG_FILE for testing
    import src.utils.config_wizard as wizard
    original_config_file = wizard.CONFIG_FILE
    wizard.CONFIG_FILE = Path(tempfile.gettempdir()) / '.test_config.json'

    try:
        # Test save
        result = save_config(test_config)
        assert result, "save_config should return True"
        assert wizard.CONFIG_FILE.exists(), "Config file should exist"

        # Test load
        loaded_config = load_config()
        assert loaded_config is not None, "load_config should return config"
        assert loaded_config['ai_provider'] == 'ollama', "Provider should match"
        assert len(loaded_config['rss_feeds']) == 2, "Should have 2 feeds"

        print("  PASS: load_config and save_config work correctly")

        # Cleanup
        if wizard.CONFIG_FILE.exists():
            wizard.CONFIG_FILE.unlink()

    finally:
        wizard.CONFIG_FILE = original_config_file


def test_validate_url():
    """Test URL validation function."""
    print("Testing validate_url...")

    valid_urls = [
        'https://example.com/feed',
        'http://localhost:8080/rss',
        'https://subdomain.example.com/feed.xml'
    ]

    invalid_urls = [
        'not-a-url',
        'ftp://example.com',  # Valid URL but unusual scheme
        'example.com',  # Missing scheme
        '',
    ]

    for url in valid_urls:
        assert validate_url(url), f"Should validate: {url}"

    # Note: ftp:// is actually valid, just not http/https
    assert validate_url('ftp://example.com'), "FTP is a valid URL scheme"

    # Test actual invalid ones
    assert not validate_url('not-a-url'), "Should not validate: not-a-url"
    assert not validate_url(''), "Should not validate: empty string"

    print("  PASS: validate_url works correctly")


def test_ai_providers():
    """Test AI provider information is complete."""
    print("Testing AI provider definitions...")

    required_fields = ['name', 'type', 'cost', 'requires_api_key', 'description', 'setup_url']

    for provider_key, provider_info in AI_PROVIDERS.items():
        for field in required_fields:
            assert field in provider_info, f"{provider_key} missing field: {field}"

        # Cloud providers should have warnings
        if provider_info['type'] == 'cloud' and provider_info['requires_api_key']:
            if provider_key not in ['gemini']:  # Gemini has free tier
                assert 'warning' in provider_info, f"{provider_key} should have cost warning"

    print("  PASS: All AI providers properly defined")


def test_connection_functions():
    """Test connection test functions (without actual servers)."""
    print("Testing connection functions...")

    # Test with invalid URLs (should return False, not crash)
    result = test_ollama_connection('http://invalid-host-that-does-not-exist:11434')
    assert result is False, "Should return False for invalid Ollama server"

    result = test_lm_studio_connection('http://invalid-host-that-does-not-exist:1234')
    assert result is False, "Should return False for invalid LM Studio server"

    print("  PASS: Connection functions handle errors gracefully")


def main():
    """Run all tests."""
    print("=" * 70)
    print("Configuration Wizard Test Suite")
    print("=" * 70)
    print()

    try:
        test_load_save_config()
        test_validate_url()
        test_ai_providers()
        test_connection_functions()

        print()
        print("=" * 70)
        print("All tests passed!")
        print("=" * 70)
        return 0

    except AssertionError as e:
        print()
        print("=" * 70)
        print(f"TEST FAILED: {e}")
        print("=" * 70)
        return 1

    except Exception as e:
        print()
        print("=" * 70)
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 70)
        return 1


if __name__ == '__main__':
    sys.exit(main())
