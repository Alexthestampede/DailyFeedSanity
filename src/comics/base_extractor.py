"""
Base extractor for webcomics
"""
from abc import ABC, abstractmethod
import os
from pathlib import Path
from ..utils.logging_config import get_logger
from ..utils.http_client import download_file

logger = get_logger(__name__)


class ComicExtractor(ABC):
    """
    Abstract base class for comic extractors.
    """

    def __init__(self, feed_data, session=None):
        """
        Initialize comic extractor.

        Args:
            feed_data: Dict containing feed information and latest entry
            session: requests.Session object for HTTP requests
        """
        self.feed_data = feed_data
        self.session = session
        self.feed_name = feed_data.get('feed_name', 'Unknown')
        self.entry = feed_data.get('entry', {})

    @abstractmethod
    def extract_image_urls(self):
        """
        Extract comic image URLs from the feed entry.

        Returns:
            List of image URL strings
        """
        pass

    def download_images(self, output_dir):
        """
        Download comic images to output directory.

        Args:
            output_dir: Directory to save images

        Returns:
            List of downloaded file paths
        """
        image_urls = self.extract_image_urls()

        if not image_urls:
            logger.warning(f"No images found for {self.feed_name}")
            return []

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        downloaded_files = []

        for i, url in enumerate(image_urls):
            try:
                # Generate filename
                if len(image_urls) == 1:
                    filename = f"{self.feed_name}.jpg"
                else:
                    # Multiple images (e.g., Penny Arcade panels)
                    filename = f"{self.feed_name}-p{i+1}.jpg"

                output_path = output_dir / filename

                # Download with retry
                success = self._download_with_retry(url, output_path)

                if success:
                    downloaded_files.append(str(output_path))
                    logger.info(f"Downloaded {self.feed_name}: {url} -> {filename}")
                else:
                    logger.error(f"Failed to download {self.feed_name}: {url}")

            except Exception as e:
                logger.error(f"Error downloading image for {self.feed_name}: {e}")

        return downloaded_files

    def _download_with_retry(self, url, output_path, max_retries=3):
        """
        Download file with retry logic.

        Args:
            url: URL to download
            output_path: Path to save file
            max_retries: Maximum number of retry attempts

        Returns:
            True if successful, False otherwise
        """
        for attempt in range(max_retries):
            try:
                success = download_file(url, output_path, session=self.session)
                if success:
                    return True
            except Exception as e:
                logger.warning(f"Download attempt {attempt + 1} failed: {e}")

        return False

    def get_comic_info(self):
        """
        Get metadata about the comic.

        Returns:
            Dict with comic metadata
        """
        return {
            'name': self.feed_name,
            'title': self.entry.get('title', ''),
            'link': self.entry.get('link', ''),
            'published': self.entry.get('published'),
        }
