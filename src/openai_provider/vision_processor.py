"""
Vision processing with OpenAI GPT-4 Vision for RSS Feed Processor

This module provides image analysis capabilities using GPT-4 Vision API.
It maintains a similar interface to OllamaVisionClient for consistency.
"""
import base64
import re
from typing import Optional
from .client import OpenAIClient
from ..utils.logging_config import get_logger
from ..utils.http_client import fetch_url
from ..config import VISION_TEMPERATURE

logger = get_logger(__name__)


class OpenAIVisionProcessor:
    """
    Vision processor using OpenAI GPT-4 Vision for image analysis.

    This class provides image analysis capabilities including OCR, image
    description, and comic validation.
    """

    def __init__(self, model: str = "gpt-4o", api_key: Optional[str] = None):
        """
        Initialize vision processor.

        Args:
            model: OpenAI vision model (gpt-4o, gpt-4-turbo, etc.)
            api_key: OpenAI API key (optional, will use env var if not provided)

        Raises:
            ValueError: If API key is not found

        Note:
            gpt-4o is recommended as it has vision capabilities and is more cost-effective
            than gpt-4-vision-preview
        """
        self.model = model
        try:
            self.client = OpenAIClient(api_key=api_key)
            logger.info(f"OpenAI vision processor initialized with model: {model}")
        except ValueError as e:
            logger.error(f"Failed to initialize OpenAI vision processor: {e}")
            raise

    def encode_image_from_url(self, image_url: str, session=None) -> Optional[str]:
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

    def encode_image_from_file(self, image_path: str) -> Optional[str]:
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

    def analyze_image(
        self,
        image_path: str,
        prompt: str,
        model: Optional[str] = None
    ) -> Optional[str]:
        """
        Analyze an image with a custom prompt using GPT-4 Vision.

        Args:
            image_path: Path to image file
            prompt: Analysis prompt
            model: Override default model (optional)

        Returns:
            Analysis result text, or None on error
        """
        model_to_use = model or self.model

        try:
            # Encode image
            encoded_image = self.encode_image_from_file(image_path)
            if not encoded_image:
                logger.error("Failed to encode image for analysis")
                return None

            # Use generate method with images parameter
            response = self.client.generate(
                model=model_to_use,
                prompt=prompt,
                temperature=VISION_TEMPERATURE,
                images=[encoded_image]
            )

            return response

        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return None

    def detect_oglaf_pages(self, arc_image_url: str, session=None) -> int:
        """
        Detect number of pages in Oglaf arc image using OCR.

        This method uses GPT-4 Vision to read pagination text from the arc
        navigation image.

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
                logger.error("No response from GPT-4 Vision")
                return 1

            # Extract number from response
            logger.debug(f"GPT-4 Vision response: {response}")
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

    def validate_comic_image(self, image_path: str) -> dict:
        """
        Validate that an image is a valid comic image.

        Uses GPT-4 Vision to verify the image is actually a comic/webcomic.

        Args:
            image_path: Path to image file

        Returns:
            dict with validation results:
                - 'valid': bool - basic validation passed
                - 'is_comic': bool - verified as comic by AI
                - 'reason': str - error message if invalid
        """
        logger.debug(f"Validating comic image: {image_path}")

        result = {
            'valid': False,
            'reason': None,
            'is_comic': False
        }

        try:
            # Basic file existence check
            with open(image_path, 'rb'):
                pass

            result['valid'] = True

            # Use GPT-4 Vision to verify it's a comic
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
                    logger.debug(f"GPT-4 Vision confirmed image is a comic: {image_path}")
                else:
                    logger.warning(f"GPT-4 Vision says image may not be a comic: {image_path}")

            return result

        except Exception as e:
            result['reason'] = f"Validation error: {e}"
            logger.error(f"Image validation failed for {image_path}: {e}")
            return result

    def describe_image(self, image_url: str, session=None) -> Optional[str]:
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

    def extract_text_from_image(self, image_path: str) -> Optional[str]:
        """
        Extract text from an image using OCR.

        Args:
            image_path: Path to image file

        Returns:
            Extracted text, or None on error
        """
        try:
            encoded_image = self.encode_image_from_file(image_path)
            if not encoded_image:
                return None

            prompt = (
                "Extract all visible text from this image. "
                "Return only the text content, no explanations."
            )

            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                temperature=VISION_TEMPERATURE,
                images=[encoded_image]
            )

            return response

        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            return None
