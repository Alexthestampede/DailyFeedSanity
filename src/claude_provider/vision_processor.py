"""
Vision processing with Anthropic Claude for RSS Feed Processor

This module provides image analysis using Anthropic's Claude vision capabilities.
"""
import base64
import requests
from pathlib import Path
from typing import Optional
from PIL import Image
from io import BytesIO
from .client import ClaudeClient
from ..utils.logging_config import get_logger
from ..config import CLAUDE_VISION_MODEL, VISION_TEMPERATURE

logger = get_logger(__name__)


class ClaudeVisionClient:
    """
    Vision processor using Anthropic Claude for image analysis.

    Claude 1.5 Flash and Pro models have built-in vision capabilities.
    """

    def __init__(self, api_key: str, model: str = CLAUDE_VISION_MODEL):
        """
        Initialize Claude vision processor.

        Args:
            api_key: Anthropic API key
            model: Claude model to use (must support vision)
        """
        self.client = ClaudeClient(api_key=api_key)
        self.model = model

    def encode_image_from_file(self, image_path: str) -> Optional[tuple[str, str]]:
        """
        Encode an image file to base64.

        Args:
            image_path: Path to image file

        Returns:
            Tuple of (base64_data, mime_type) or None on error
        """
        try:
            path = Path(image_path)
            if not path.exists():
                logger.error(f"Image file not found: {image_path}")
                return None

            # Determine MIME type from extension
            ext = path.suffix.lower()
            mime_types = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.webp': 'image/webp'
            }
            mime_type = mime_types.get(ext, 'image/jpeg')

            # Read and encode image
            with open(image_path, 'rb') as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')

            return image_data, mime_type

        except Exception as e:
            logger.error(f"Error encoding image from file: {e}")
            return None

    def encode_image_from_url(self, image_url: str) -> Optional[tuple[str, str]]:
        """
        Download and encode an image from URL.

        Args:
            image_url: URL of the image

        Returns:
            Tuple of (base64_data, mime_type) or None on error
        """
        try:
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()

            # Get MIME type from response headers
            content_type = response.headers.get('content-type', 'image/jpeg')
            mime_type = content_type.split(';')[0].strip()

            # Encode image data
            image_data = base64.b64encode(response.content).decode('utf-8')

            return image_data, mime_type

        except Exception as e:
            logger.error(f"Error encoding image from URL: {e}")
            return None

    def analyze_image(self, image_path: str, prompt: str, model: Optional[str] = None) -> Optional[str]:
        """
        Analyze an image with a custom prompt.

        Args:
            image_path: Path to image file or URL
            prompt: Analysis prompt
            model: Model to use (optional)

        Returns:
            Analysis result or None on error
        """
        model = model or self.model

        # Determine if image_path is a URL or file path
        if image_path.startswith('http://') or image_path.startswith('https://'):
            encoded = self.encode_image_from_url(image_path)
        else:
            encoded = self.encode_image_from_file(image_path)

        if not encoded:
            logger.error("Failed to encode image")
            return None

        image_data, mime_type = encoded

        try:
            result = self.client.generate_with_image(
                prompt=prompt,
                image_data=image_data,
                temperature=VISION_TEMPERATURE,
                model=model,
                mime_type=mime_type
            )

            return result

        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return None

    def detect_oglaf_pages(self, image_url: str) -> bool:
        """
        Detect if an Oglaf comic has multiple pages.

        Args:
            image_url: URL of the comic image

        Returns:
            True if multiple pages detected, False otherwise
        """
        prompt = (
            "Does this image contain navigation arrows, 'next page' indicators, "
            "or other signs that there are more pages to this comic? "
            "Answer with only 'yes' or 'no'."
        )

        result = self.analyze_image(image_url, prompt)

        if result:
            return result.strip().lower() == 'yes'

        return False

    def validate_comic_image(self, image_path: str) -> bool:
        """
        Validate that an image is actually a comic (not a thumbnail or error page).

        Args:
            image_path: Path to image file

        Returns:
            True if image appears to be a valid comic, False otherwise
        """
        prompt = (
            "Is this a full comic strip or panel? (not a thumbnail, not an error page, "
            "not a 'comic not found' message). Answer with only 'yes' or 'no'."
        )

        result = self.analyze_image(image_path, prompt)

        if result:
            return result.strip().lower() == 'yes'

        return False

    def describe_image(self, image_path: str) -> Optional[str]:
        """
        Get a description of what's in the image.

        Args:
            image_path: Path to image file or URL

        Returns:
            Image description or None on error
        """
        prompt = "Describe what you see in this image in detail."

        return self.analyze_image(image_path, prompt)
