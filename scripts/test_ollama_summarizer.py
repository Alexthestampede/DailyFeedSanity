#!/usr/bin/env python3
"""
Standalone test script for AI summarizer (Ollama, LM Studio, etc.)

Usage:
    python scripts/test_ollama_summarizer.py <url>
    python scripts/test_ollama_summarizer.py <url> --author "Francesca Testa"
    python scripts/test_ollama_summarizer.py <url> --model "G47bLDMC" --verbose
    python scripts/test_ollama_summarizer.py <url> --ai-provider lm_studio
"""
import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.news.article_extractor import ArticleExtractor
from src.news.content_cleaner import ContentCleaner
from src.ai_client import create_ai_client_with_fallback
from src.config import TEXT_MODEL, CLICKBAIT_AUTHORS, AI_PROVIDER


def print_separator(char='=', length=80):
    """Print a separator line."""
    print(char * length)


def print_section(title):
    """Print a section header."""
    print()
    print_separator()
    print(f" {title}")
    print_separator()
    print()


def main():
    """Main test function."""
    parser = argparse.ArgumentParser(
        description='Test AI summarizer (Ollama, LM Studio, etc.) with a URL',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  %(prog)s https://example.com/article

  # Test with clickbait author
  %(prog)s https://example.com/article --author "Francesca Testa"

  # Verbose output with custom model
  %(prog)s https://example.com/article --model "G47bLDMC" --verbose

  # Use LM Studio instead of Ollama
  %(prog)s https://example.com/article --ai-provider lm_studio
        """
    )

    parser.add_argument(
        'url',
        help='URL of the article to summarize'
    )

    parser.add_argument(
        '--author',
        type=str,
        help='Author name (for clickbait detection)'
    )

    parser.add_argument(
        '--model',
        type=str,
        default=TEXT_MODEL,
        help=f'AI model to use (default: {TEXT_MODEL})'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed information'
    )

    parser.add_argument(
        '--ai-provider',
        type=str,
        choices=['ollama', 'lm_studio', 'lmstudio'],
        help=f'AI provider to use (default: {AI_PROVIDER}). Overrides config.AI_PROVIDER'
    )

    args = parser.parse_args()

    # Override AI provider if specified
    provider_name = AI_PROVIDER
    if args.ai_provider:
        import src.config as config_module
        config_module.AI_PROVIDER = args.ai_provider
        provider_name = args.ai_provider

    # Print header
    print_section("AI Summarizer Test")
    print(f"URL: {args.url}")
    print(f"Provider: {provider_name}")
    print(f"Model: {args.model}")
    if args.author:
        print(f"Author: {args.author}")
        if args.author in CLICKBAIT_AUTHORS:
            print("  (Clickbait author detected - will use special prompt)")

    # Initialize AI clients using factory
    print_section(f"Checking {provider_name} Server")
    try:
        ai_client, text_processor, vision_processor = create_ai_client_with_fallback()
    except Exception as e:
        print(f"ERROR: Failed to initialize AI client: {e}")
        return 1

    if not ai_client.health_check():
        print(f"ERROR: {provider_name} server is not available!")
        print(f"Please start {provider_name} and try again.")
        return 1

    print(f"{provider_name} server is available")

    # List models
    models = ai_client.list_models()
    print(f"Available models: {', '.join(models)}")

    if args.model not in models:
        print(f"WARNING: Model '{args.model}' not found in available models")

    # Extract article
    print_section("Extracting Article")
    extractor = ArticleExtractor()

    try:
        article_data = extractor.extract_from_url(args.url)

        if not article_data:
            print("ERROR: Failed to extract article")
            return 1

        print(f"Title: {article_data.get('title', 'N/A')}")
        print(f"Author: {article_data.get('author', 'N/A')}")
        print(f"Date: {article_data.get('date', 'N/A')}")
        print(f"Text length: {len(article_data.get('text', ''))} characters")

        if args.verbose:
            print("\nFirst 500 characters:")
            print(article_data.get('text', '')[:500])

    except Exception as e:
        print(f"ERROR: Failed to extract article: {e}")
        return 1

    # Clean content
    print_section("Cleaning Content")
    cleaner = ContentCleaner()

    cleaned_text = cleaner.clean_text(article_data['text'])
    print(f"Cleaned text length: {len(cleaned_text)} characters")

    # Validate content
    validation = cleaner.validate_article_content(cleaned_text)
    print(f"Validation: {'PASSED' if validation['valid'] else 'FAILED'}")
    print(f"Word count: {validation['word_count']}")
    print(f"Character count: {validation['char_count']}")

    if not validation['valid']:
        print(f"Reason: {validation['reason']}")
        return 1

    if args.verbose:
        print("\nFirst 500 characters of cleaned text:")
        print(cleaned_text[:500])

    # Generate summary
    print_section("Generating Summary")

    # Override author if specified
    author = args.author or article_data.get('author')
    title = article_data.get('title', '')

    try:
        summary_data = text_processor.generate_summary(cleaned_text, title=title, author=author)

        if not summary_data:
            print("ERROR: Failed to generate summary")
            return 1

        print("Summary generated successfully!")
        print(f"Is clickbait: {summary_data.get('is_clickbait', False)}")
        if summary_data.get('clickbait_detected_by'):
            print(f"Detected by: {summary_data.get('clickbait_detected_by')}")

    except Exception as e:
        print(f"ERROR: Failed to generate summary: {e}")
        return 1

    # Display results
    print_section("Results")

    print(f"Original Title: {article_data.get('title', 'N/A')}")
    print()
    print(f"Generated Title: {summary_data['title']}")
    print()
    print("Summary:")
    print_separator('-')
    print(summary_data['summary'])
    print_separator('-')

    # Statistics
    print_section("Statistics")
    print(f"Original text: {len(cleaned_text)} characters, {validation['word_count']} words")
    print(f"Summary: {len(summary_data['summary'])} characters")
    print(f"Compression ratio: {len(summary_data['summary']) / len(cleaned_text) * 100:.1f}%")

    print_section("Test Complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
