"""
Comic downloader for RSS Feed Processor
"""
from pathlib import Path
from PIL import Image
from .extractors import get_extractor
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class ComicDownloader:
    """
    Downloads and validates comic images.
    """

    def __init__(self, validate_images=False, use_vision=True, vision_processor=None):
        """
        Initialize comic downloader.

        Args:
            validate_images: Whether to validate images with vision model
            use_vision: Whether to use vision model for Oglaf multi-page detection
            vision_processor: DomainVisionProcessor instance (optional)
        """
        self.validate_images = validate_images
        self.use_vision = use_vision
        self.vision_processor = vision_processor

    def download_comic(self, feed_data, output_dir):
        """
        Download comic images for a feed.

        Args:
            feed_data: Feed data dict
            output_dir: Output directory for images

        Returns:
            dict with download results
        """
        feed_name = feed_data.get('feed_name', 'Unknown')
        logger.info(f"Downloading comic: {feed_name}")

        try:
            # Get appropriate extractor
            extractor = get_extractor(
                feed_data,
                session=feed_data.get('session'),
                use_vision=self.use_vision,
                vision_processor=self.vision_processor
            )

            # Download images
            downloaded_files = extractor.download_images(output_dir)

            if not downloaded_files:
                logger.warning(f"No images downloaded for {feed_name}")
                return {
                    'success': False,
                    'feed_name': feed_name,
                    'error': 'No images found'
                }

            # Validate images if requested
            if self.validate_images and self.vision_processor:
                validation_results = self._validate_images(downloaded_files)
            else:
                validation_results = None

            # Get comic info
            comic_info = extractor.get_comic_info()

            result = {
                'success': True,
                'feed_name': feed_name,
                'comic_info': comic_info,
                'images': downloaded_files,
                'image_count': len(downloaded_files),
                'validation': validation_results
            }

            logger.info(f"Successfully downloaded {len(downloaded_files)} image(s) for {feed_name}")
            return result

        except Exception as e:
            logger.error(f"Error downloading comic {feed_name}: {e}")
            return {
                'success': False,
                'feed_name': feed_name,
                'error': str(e)
            }

    def _validate_images(self, image_paths):
        """
        Validate downloaded images.

        Args:
            image_paths: List of image file paths

        Returns:
            List of validation results
        """
        if not self.vision_processor:
            return None

        results = []

        for image_path in image_paths:
            try:
                validation = self.vision_processor.validate_comic_image(image_path)
                results.append({
                    'path': image_path,
                    'valid': validation['valid'],
                    'is_comic': validation.get('is_comic', False),
                    'format': validation.get('format'),
                    'size': validation.get('size'),
                    'reason': validation.get('reason')
                })
            except Exception as e:
                logger.error(f"Error validating image {image_path}: {e}")
                results.append({
                    'path': image_path,
                    'valid': False,
                    'error': str(e)
                })

        return results

    def verify_image_format(self, image_path):
        """
        Verify image is in a valid format.

        Args:
            image_path: Path to image file

        Returns:
            True if valid, False otherwise
        """
        try:
            with Image.open(image_path) as img:
                img.verify()
                return True
        except Exception as e:
            logger.error(f"Invalid image format for {image_path}: {e}")
            return False

    def batch_download(self, comic_feeds, output_dir):
        """
        Download multiple comics.

        Args:
            comic_feeds: List of feed data dicts (each with 'entries' list)
            output_dir: Output directory

        Returns:
            List of download results
        """
        results = []

        for feed_data in comic_feeds:
            entries = feed_data.get('entries', [])
            if entries:
                single_entry_data = {
                    **feed_data,
                    'entry': entries[0]
                }
                result = self.download_comic(single_entry_data, output_dir)
                results.append(result)
            else:
                logger.warning(f"No entries for {feed_data.get('feed_name', 'Unknown')}")

        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        logger.info(f"Batch download complete: {successful} successful, {failed} failed")

        return results
