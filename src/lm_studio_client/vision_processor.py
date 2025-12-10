"""
Vision processing with LM Studio for RSS Feed Processor

This module provides image analysis using LM Studio's OpenAI-compatible API
with vision models. It maintains the same interface as the Ollama vision
processor for seamless provider switching.
"""
import base64
import re
from typing import Optional, Dict, Any
from PIL import Image
from .client import LMStudioClient
from ..utils.logging_config import get_logger
from ..utils.http_client import fetch_url
from ..config import (
    LM_STUDIO_VISION_MODEL,
    VISION_TEMPERATURE,
    MIN_IMAGE_SIZE,
    ALLOWED_IMAGE_FORMATS
)

logger = get_logger(__name__)


class LMStudioVisionClient:
    """
    Vision processor using LM Studio for image analysis.

    This class implements the same interface as OllamaVisionClient, allowing
    for transparent provider switching.
    """

    def __init__(self, model=LM_STUDIO_VISION_MODEL, base_url=None):
        """
        Initialize vision processor.

        Args:
            model: LM Studio model name for vision processing
            base_url: LM Studio server base URL (optional, uses config default if not provided)
        """
        self.model = model
        if base_url:
            self.client = LMStudioClient(base_url=base_url)
        else:
            self.client = LMStudioClient()
        logger.info(f"Initialized LM Studio vision client with model: {model}")

    def encode_image_from_url(self, image_url, session=None):
        """
        Download and encode image from URL to base64.

        Args:
            image_url: URL of image to download
            session: requests.Session object

        Returns:
            Base64-encoded image string, or None on error
        """
        try:
            response = fetch_url(image_url, session=session)
            image_data = response.content

            # Encode to base64
            encoded = base64.b64encode(image_data).decode('utf-8')
            logger.debug(f"Encoded image from {image_url}")
            return encoded

        except Exception as e:
            logger.error(f"Failed to encode image from {image_url}: {e}")
            return None

    def encode_image_from_file(self, image_path):
        """
        Encode image from file to base64.

        Args:
            image_path: Path to image file

        Returns:
            Base64-encoded image string, or None on error
        """
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()

            encoded = base64.b64encode(image_data).decode('utf-8')
            logger.debug(f"Encoded image from {image_path}")
            return encoded

        except Exception as e:
            logger.error(f"Failed to encode image from {image_path}: {e}")
            return None

    def analyze_image(self, image_path: str, prompt: str, model: Optional[str] = None) -> Optional[str]:
        """
        Analyze an image with a custom prompt.

        Args:
            image_path: Path to image file
            prompt: Analysis prompt
            model: Optional model override (uses self.model if None)

        Returns:
            Analysis result string, or None on error
        """
        try:
            # Encode the image
            encoded_image = self.encode_image_from_file(image_path)
            if not encoded_image:
                logger.error(f"Failed to encode image: {image_path}")
                return None

            # Use specified model or default
            use_model = model if model else self.model

            # Generate response using vision model
            response = self.client.generate(
                model=use_model,
                prompt=prompt,
                temperature=VISION_TEMPERATURE,
                images=[encoded_image]
            )

            if not response:
                logger.error("No response from LM Studio vision model")
                return None

            logger.debug(f"Image analysis completed: {len(response)} characters")
            return response

        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return None

    def detect_oglaf_pages(self, arc_image_url, session=None):
        """
        Detect number of pages in Oglaf arc image using OCR.

        Args:
            arc_image_url: URL of the arc image showing page count
            session: requests.Session object

        Returns:
            Number of pages (int), or 1 on error
        """
        logger.info(f"Detecting Oglaf page count from arc image: {arc_image_url}")

        try:
            # Encode image
            encoded_image = self.encode_image_from_url(arc_image_url, session=session)
            if not encoded_image:
                logger.error("Failed to encode arc image")
                return 1

            # Prompt for OCR
            prompt = (
                "This is a navigation arc image from a webcomic showing page numbers. "
                "It contains text like 'Page 1 of X' or similar pagination information. "
                "Extract the total number of pages from this image. "
                "Respond with ONLY the number, nothing else."
            )

            # Use vision model to OCR the image
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                temperature=VISION_TEMPERATURE,
                images=[encoded_image]
            )

            if not response:
                logger.error("No response from LM Studio vision model")
                return 1

            # Extract number from response
            logger.debug(f"Vision model response: {response}")
            numbers = re.findall(r'\d+', response)

            if numbers:
                page_count = int(numbers[-1])  # Take the last number (usually "X of Y")
                logger.info(f"Detected {page_count} pages in Oglaf comic")
                return page_count
            else:
                logger.warning("Could not extract page count, defaulting to 1")
                return 1

        except Exception as e:
            logger.error(f"Error detecting Oglaf pages: {e}")
            return 1

    def validate_comic_image(self, image_path):
        """
        Validate that an image is a valid comic image.

        Args:
            image_path: Path to image file

        Returns:
            dict with validation results
        """
        logger.debug(f"Validating comic image: {image_path}")

        result = {
            'valid': False,
            'reason': None,
            'format': None,
            'size': None,
            'is_comic': False
        }

        try:
            # Check if file exists and is readable
            with Image.open(image_path) as img:
                result['format'] = img.format
                result['size'] = img.size

                # Check format
                if img.format not in ALLOWED_IMAGE_FORMATS:
                    result['reason'] = f"Invalid format: {img.format}"
                    return result

                # Check minimum size
                width, height = img.size
                if width < MIN_IMAGE_SIZE or height < MIN_IMAGE_SIZE:
                    result['reason'] = f"Image too small: {width}x{height}"
                    return result

                result['valid'] = True

                # Optional: Use vision model to verify it's actually a comic
                # This is expensive, so only use if explicitly requested
                encoded_image = self.encode_image_from_file(image_path)
                if encoded_image:
                    prompt = (
                        "Is this image a webcomic or comic strip? "
                        "Answer with only 'yes' or 'no'."
                    )

                    response = self.client.generate(
                        model=self.model,
                        prompt=prompt,
                        temperature=VISION_TEMPERATURE,
                        images=[encoded_image]
                    )

                    if response and 'yes' in response.lower():
                        result['is_comic'] = True

                logger.debug(f"Image validation passed: {image_path}")
                return result

        except Exception as e:
            result['reason'] = f"Validation error: {e}"
            logger.error(f"Image validation failed for {image_path}: {e}")
            return result

    def describe_image(self, image_url, session=None):
        """
        Generate a description of an image.

        Args:
            image_url: URL of image
            session: requests.Session object

        Returns:
            Description string, or None on error
        """
        try:
            encoded_image = self.encode_image_from_url(image_url, session=session)
            if not encoded_image:
                return None

            prompt = "Describe this image in detail."

            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                temperature=VISION_TEMPERATURE,
                images=[encoded_image]
            )

            return response

        except Exception as e:
            logger.error(f"Error describing image: {e}")
            return None
