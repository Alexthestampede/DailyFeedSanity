#!/usr/bin/env python3
"""
Test script for LM Studio vision model support.

Uses the factory pattern to create AI client with LM Studio provider.

Usage:
    python scripts/test_lm_studio_vision.py <image_path> [prompt]
"""
import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import src.config as config_module
config_module.AI_PROVIDER = 'lm_studio'

from src.ai_client import create_ai_client_with_fallback
from src.config import LM_STUDIO_BASE_URL


def main():
    """Main test function."""
    parser = argparse.ArgumentParser(description='Test LM Studio vision model with an image')
    parser.add_argument('image_path', help='Path to the image file')
    parser.add_argument('prompt', nargs='?', default="Describe this image in detail.",
                        help='Prompt for image analysis')
    parser.add_argument('--validate', action='store_true', help='Run comic image validation')
    args = parser.parse_args()

    image_path = Path(args.image_path)
    if not image_path.exists():
        print(f"ERROR: Image file not found: {args.image_path}")
        return 1

    print(f"\nLM Studio Vision Test")
    print(f"Image: {args.image_path}")
    print(f"Server: {LM_STUDIO_BASE_URL}")

    try:
        ai_client, text_processor, vision_processor = create_ai_client_with_fallback()
    except Exception as e:
        print(f"ERROR: Failed to create AI client: {e}")
        return 1

    if not vision_processor:
        print("ERROR: No vision processor available")
        return 1

    if args.validate:
        result = vision_processor.validate_comic_image(str(image_path))
        print(f"Valid: {result['valid']}, Format: {result['format']}, "
              f"Size: {result['size']}, Is Comic: {result['is_comic']}")
    else:
        encoded = vision_processor.encode_image_from_file(str(image_path))
        if not encoded:
            print("ERROR: Failed to encode image")
            return 1
        response = vision_processor.processor.analyze_image(
            image_data=encoded, prompt=args.prompt
        )
        if response:
            print(f"\nResult:\n{response}")
        else:
            print("ERROR: No response")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
