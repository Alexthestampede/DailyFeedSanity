#!/usr/bin/env python3
"""
Test script for LM Studio vision model support

Usage:
    python scripts/test_lm_studio_vision.py <image_path> [prompt]

Example:
    python scripts/test_lm_studio_vision.py /path/to/image.jpg "What is in this image?"
    python scripts/test_lm_studio_vision.py /path/to/comic.png "Is this a comic?"
"""
import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.lm_studio_client.vision_processor import LMStudioVisionClient
from src.config import LM_STUDIO_VISION_MODEL, LM_STUDIO_BASE_URL


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
        description='Test LM Studio vision model with an image',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic image description
  %(prog)s /path/to/image.jpg

  # Custom prompt
  %(prog)s /path/to/comic.png "Is this a comic strip?"

  # Validate comic image
  %(prog)s /path/to/comic.jpg "Describe this webcomic in detail"
        """
    )

    parser.add_argument(
        'image_path',
        help='Path to the image file'
    )

    parser.add_argument(
        'prompt',
        nargs='?',
        default="Describe this image in detail.",
        help='Prompt for image analysis (default: "Describe this image in detail.")'
    )

    parser.add_argument(
        '--model',
        type=str,
        default=LM_STUDIO_VISION_MODEL,
        help=f'Vision model to use (default: {LM_STUDIO_VISION_MODEL})'
    )

    parser.add_argument(
        '--validate',
        action='store_true',
        help='Run comic image validation instead of custom prompt'
    )

    args = parser.parse_args()

    # Verify image exists
    image_path = Path(args.image_path)
    if not image_path.exists():
        print(f"ERROR: Image file not found: {args.image_path}")
        return 1

    # Print header
    print_section("LM Studio Vision Model Test")
    print(f"Image: {args.image_path}")
    print(f"Model: {args.model}")
    print(f"Server: {LM_STUDIO_BASE_URL}")
    if not args.validate:
        print(f"Prompt: {args.prompt}")

    # Initialize vision client
    print_section("Initializing LM Studio Vision Client")
    try:
        vision_client = LMStudioVisionClient(model=args.model)
        print("Vision client initialized successfully")
    except Exception as e:
        print(f"ERROR: Failed to initialize vision client: {e}")
        return 1

    # Check LM Studio availability
    if not vision_client.client.health_check():
        print("ERROR: LM Studio server is not available!")
        print(f"Please start LM Studio at {LM_STUDIO_BASE_URL} and try again.")
        return 1

    print("LM Studio server is available")

    # List available models
    models = vision_client.client.list_models()
    print(f"Available models: {', '.join(models)}")

    if args.model not in models:
        print(f"WARNING: Model '{args.model}' not found in available models")
        print("Make sure the vision model is loaded in LM Studio")

    # Test vision processing
    if args.validate:
        print_section("Running Image Validation")
        try:
            result = vision_client.validate_comic_image(str(image_path))

            print("Validation Results:")
            print(f"  Valid: {result['valid']}")
            print(f"  Format: {result['format']}")
            print(f"  Size: {result['size']}")
            print(f"  Is Comic: {result['is_comic']}")
            if result['reason']:
                print(f"  Reason: {result['reason']}")

        except Exception as e:
            print(f"ERROR: Image validation failed: {e}")
            return 1
    else:
        print_section("Analyzing Image")
        try:
            response = vision_client.analyze_image(
                str(image_path),
                args.prompt,
                model=args.model
            )

            if not response:
                print("ERROR: Failed to analyze image")
                return 1

            print("Analysis Result:")
            print_separator('-')
            print(response)
            print_separator('-')

        except Exception as e:
            print(f"ERROR: Image analysis failed: {e}")
            return 1

    print_section("Test Complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
