#!/usr/bin/env python3
"""
RSS Feed Processor - Main Entry Point

Processes RSS feeds, downloads webcomics, summarizes news articles,
and generates HTML digest page.
"""
import argparse
import sys
from datetime import datetime
from pathlib import Path

from .config import (
    OUTPUT_DIR,
    TEMP_DIR,
    RSS_FILE,
    VALIDATE_IMAGES,
    AI_PROVIDER
)
from .utils.logging_config import setup_logging, get_logger
from .utils.file_manager import SafeFileManager
from .utils.config_wizard import load_config, should_run_first_setup
from .feed_processor.feed_manager import FeedManager
from .comics.downloader import ComicDownloader
from .news.summarizer import NewsSummarizer
from .output.html_generator import HTMLGenerator
from .ai_client import create_ai_client_with_fallback

logger = None  # Will be initialized in main()


def parse_arguments():
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace with parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='RSS Feed Processor - Download webcomics and summarize news articles using AI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                              # Process all feeds (Ollama, 24h news filter)
  %(prog)s --debug                      # Enable debug logging
  %(prog)s --ai-provider gemini         # Use Google Gemini (free tier available)
  %(prog)s --ai-provider lm_studio      # Use LM Studio local server
  %(prog)s --all-entries                # Process ALL news articles (not just 24h)
  %(prog)s --validate-images            # Enable image validation with vision model
  %(prog)s --feeds custom_feeds.txt     # Use custom feed list

AI Providers (use --ai-provider):
  ollama      Local, free (default) - Requires Ollama server running
  lm_studio   Local, free - Requires LM Studio server running
  openai      Cloud, paid - Requires OPENAI_API_KEY environment variable
  gemini      Cloud, free tier + paid - Requires GEMINI_API_KEY env variable
  claude      Cloud, paid - Requires ANTHROPIC_API_KEY environment variable

Documentation:
  README.md        - Main documentation and overview
  QUICKSTART.md    - Quick setup guide for beginners
  AI_PROVIDERS.md  - Detailed AI provider comparison and setup instructions
  CLAUDE.md        - Developer reference and architecture details

Output:
  Creates output/YYYY-MM-DD/index.html with comics and article summaries
  Dark mode supported (follows system preference)
        """
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )

    parser.add_argument(
        '--validate-images',
        action='store_true',
        default=VALIDATE_IMAGES,
        help='Validate comic images using vision model (slower but more thorough)'
    )

    parser.add_argument(
        '--feeds',
        type=str,
        default=RSS_FILE,
        help=f'Path to feed list file (default: {RSS_FILE})'
    )

    parser.add_argument(
        '--output',
        type=str,
        default=OUTPUT_DIR,
        help=f'Output directory (default: {OUTPUT_DIR})'
    )

    parser.add_argument(
        '--no-vision',
        action='store_true',
        help='Disable vision model for Oglaf multi-page detection'
    )

    parser.add_argument(
        '--all-entries',
        action='store_true',
        help='Process all entries from news feeds (default: only last 24 hours)'
    )

    parser.add_argument(
        '--ai-provider',
        type=str,
        choices=['ollama', 'lm_studio', 'lmstudio', 'openai', 'gemini', 'claude', 'anthropic'],
        help=f'AI provider to use (default: {AI_PROVIDER}). Overrides config.AI_PROVIDER'
    )

    return parser.parse_args()


def check_ai_availability(ai_client, provider_name):
    """
    Check if AI server is available.

    Args:
        ai_client: AI client instance (BaseAIClient)
        provider_name: Name of the provider for logging

    Returns:
        True if available, False otherwise
    """
    logger.info(f"Checking {provider_name} server availability...")

    if not ai_client.health_check():
        logger.error(f"{provider_name} server is not available. Please start {provider_name} and try again.")
        return False

    # List available models
    models = ai_client.list_models()
    logger.info(f"Available {provider_name} models: {', '.join(models)}")

    return True


def main():
    """
    Main entry point.
    """
    global logger

    # Parse arguments
    args = parse_arguments()

    # Setup logging
    logger = setup_logging(debug=args.debug)

    logger.info("="*60)
    logger.info("RSS Feed Processor Starting")
    logger.info("="*60)

    # Check for first-time setup
    if should_run_first_setup():
        logger.info("First-time setup required")
        print("\n" + "="*60)
        print("FIRST-TIME SETUP")
        print("="*60)
        print("\nIt looks like this is your first time running the RSS Feed Processor.")
        print("Would you like to run the interactive configuration wizard?")
        print("\nThe wizard will help you:")
        print("  - Select an AI provider (Ollama, LM Studio, OpenAI, Gemini, or Claude)")
        print("  - Configure your models and connection settings")
        print("  - Add RSS feeds to process")
        print("\nYou can also skip this and configure manually in src/config.py")
        print("\nRun the wizard now? [Y/n]: ", end="")

        response = input().strip().lower()
        if response in ['', 'y', 'yes']:
            print("\nLaunching configuration wizard...")
            print("Run: python -m src.utils.config_wizard\n")
            logger.info("User chose to run configuration wizard")
            sys.exit(0)
        else:
            print("\nSkipping wizard. You can run it later with:")
            print("  python -m src.utils.config_wizard")
            print("\nContinuing with default configuration...\n")
            logger.info("User skipped first-time setup wizard")

    try:
        # Override AI provider if specified via CLI
        provider_name = AI_PROVIDER
        if args.ai_provider:
            import src.config as config_module
            original_provider = config_module.AI_PROVIDER
            config_module.AI_PROVIDER = args.ai_provider
            provider_name = args.ai_provider
            logger.info(f"AI provider overridden from '{original_provider}' to '{provider_name}' via CLI argument")

        # Initialize AI clients using factory
        logger.info(f"Initializing AI client (provider: {provider_name})...")
        try:
            ai_client, text_processor, vision_processor = create_ai_client_with_fallback()
            logger.info(f"AI client initialized successfully using {provider_name}")
            if vision_processor:
                logger.info(f"Vision processor available for {provider_name}")
        except Exception as e:
            logger.error(f"Failed to initialize AI client: {e}")
            sys.exit(1)

        # Check AI availability
        if not check_ai_availability(ai_client, provider_name):
            logger.error(f"{provider_name} server not available. Exiting.")
            sys.exit(1)

        # Initialize file manager
        file_manager = SafeFileManager(args.output, TEMP_DIR)

        # Create dated output folder
        output_folder = file_manager.create_dated_folder()
        logger.info(f"Output folder: {output_folder}")

        # Load feed URLs
        logger.info(f"Loading feeds from {args.feeds}")
        feed_manager = FeedManager()
        feed_urls = feed_manager.load_feeds_from_file(args.feeds)

        if not feed_urls:
            logger.error(f"No feeds found in {args.feeds}")
            sys.exit(1)

        logger.info(f"Loaded {len(feed_urls)} feeds")

        # Process all feeds concurrently
        logger.info("Starting concurrent feed processing...")
        processing_results = feed_manager.process_all_feeds(feed_urls, all_entries=args.all_entries)

        summary = processing_results.get_summary()
        logger.info(f"Feed processing complete: {summary}")

        # Separate comics and articles
        comic_feeds = processing_results.comics
        article_feeds = processing_results.articles

        logger.info(f"Comics: {len(comic_feeds)}, Articles: {len(article_feeds)}")

        # Process comics
        comic_results = []
        if comic_feeds:
            logger.info("Downloading comics...")
            use_vision = not args.no_vision
            comic_downloader = ComicDownloader(
                validate_images=args.validate_images,
                use_vision=use_vision
            )
            comic_results = comic_downloader.batch_download(comic_feeds, output_folder)

            successful_comics = sum(1 for r in comic_results if r.get('success', False))
            logger.info(f"Comic downloads complete: {successful_comics}/{len(comic_feeds)} successful")

        # Process news articles
        article_results = []
        if article_feeds:
            logger.info("Processing news articles...")
            news_summarizer = NewsSummarizer(text_processor=text_processor)
            article_results = news_summarizer.batch_process(article_feeds)

            successful_articles = sum(1 for r in article_results if r.get('success', False))
            logger.info(f"Article processing complete: {successful_articles}/{len(article_feeds)} successful")

        # Generate HTML output
        logger.info("Generating HTML output...")
        html_generator = HTMLGenerator()
        html_path = html_generator.generate(
            processing_results,
            comic_results,
            article_results,
            output_folder
        )

        logger.info("="*60)
        logger.info("Processing Complete!")
        logger.info("="*60)
        logger.info(f"Output: {html_path}")
        logger.info(f"Comics: {len([r for r in comic_results if r.get('success', False)])}")
        logger.info(f"Articles: {len([r for r in article_results if r.get('success', False)])}")
        logger.info(f"Errors: {len(processing_results.errors)}")

        if processing_results.errors:
            logger.warning("Some feeds had errors. Check the HTML output for details.")

        # Cleanup old temp folders (older than 7 days)
        try:
            file_manager.cleanup_old_temp_folders(days=7)
        except Exception as e:
            logger.warning(f"Error cleaning up old temp folders: {e}")

        logger.info("="*60)
        return 0

    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        return 130

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
