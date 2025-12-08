"""
Comic-specific extractors for RSS Feed Processor
"""
import re
from bs4 import BeautifulSoup
from .base_extractor import ComicExtractor
from ..utils.logging_config import get_logger
from ..utils.http_client import fetch_url
from ..ollama_client.vision_processor import OllamaVisionClient

logger = get_logger(__name__)


class DefaultExtractor(ComicExtractor):
    """
    Default extractor for standard RSS feeds with <img src="..."> tags.
    """

    def extract_image_urls(self):
        """Extract image from RSS description/content."""
        content = self.entry.get('content') or self.entry.get('description', '')

        if not content:
            logger.warning(f"No content found for {self.feed_name}")
            return []

        # Look for img tags
        match = re.search(r'<img\s+[^>]*src="([^"]+)"', content)

        if match:
            image_url = match.group(1)

            # Remove WordPress thumbnail dimensions (e.g., -150x150, -300x200)
            image_url = re.sub(r'-\d+x\d+(\.(png|jpg|jpeg|gif))', r'\1', image_url)

            logger.debug(f"Found image URL in {self.feed_name}: {image_url}")
            return [image_url]

        logger.warning(f"No image found in content for {self.feed_name}")
        return []


class PennyArcadeExtractor(ComicExtractor):
    """
    Penny Arcade extractor - downloads all three panels (p1, p2, p3).
    Note: RSS has news posts first, need to find comic entry with /comic/ in URL.
    """

    def extract_image_urls(self):
        """Extract Penny Arcade comic panels."""
        comic_page_url = self.entry.get('link')

        # Penny Arcade RSS mixes news and comics, skip if not a comic URL
        if not comic_page_url or '/comic/' not in comic_page_url:
            logger.debug(f"Skipping non-comic Penny Arcade link: {comic_page_url}")
            # This isn't a comic, it's a news post - return empty to skip
            return []

        try:
            # Fetch comic page
            response = fetch_url(comic_page_url, session=self.session)
            html_content = response.text

            # Penny Arcade format changed - now uses single image (no more p1/p2/p3)
            # Try new format first: assets.penny-arcade.com/comics/YYYYMMDD-XXXXXXXX.jpg
            match = re.search(r'(https://assets\.penny-arcade\.com/comics/\d{8}-[a-zA-Z0-9]+\.jpg)', html_content)

            if match:
                comic_url = match.group(1)
                logger.debug(f"Found Penny Arcade comic: {comic_url}")
                return [comic_url]

            # Fallback to old multi-panel format (p1, p2, p3)
            match = re.search(r'src="(https://assets\.penny-arcade\.com/comics/.*?p1.*?)"', html_content)

            if match:
                panel1_url = match.group(1)
                logger.debug(f"Found Penny Arcade panel 1 (old format): {panel1_url}")

                # Generate URLs for other panels
                panel2_url = panel1_url.replace('p1', 'p2')
                panel3_url = panel1_url.replace('p1', 'p3')

                return [panel1_url, panel2_url, panel3_url]

            logger.warning("Could not find Penny Arcade comic image")
            return []

        except Exception as e:
            logger.error(f"Error extracting Penny Arcade comic: {e}")
            return []


class OglafExtractor(ComicExtractor):
    """
    Oglaf extractor - handles multi-page comics using vision model.
    """

    def __init__(self, feed_data, session=None, use_vision=True):
        """
        Initialize Oglaf extractor.

        Args:
            feed_data: Feed data dict
            session: HTTP session
            use_vision: Whether to use vision model for page detection
        """
        super().__init__(feed_data, session)
        self.use_vision = use_vision
        self.vision_client = OllamaVisionClient() if use_vision else None

    def extract_image_urls(self):
        """Extract Oglaf comic images. Pattern: media.oglaf.com/comic/NAME.jpg (tt prefix = title card)"""
        main_page_url = "https://www.oglaf.com/"

        try:
            # Fetch main page - may redirect to age-confirmation
            response = fetch_url(main_page_url, session=self.session, allow_redirects=True)
            html_content = response.text

            # Look for comic pattern: media.oglaf.com/comic/XXXXX.jpg
            # Skip title cards (ttXXXXX.jpg)
            comics = re.findall(r'(https?://media\.oglaf\.com/comic/(?!tt)[^"]+\.jpg)', html_content)

            if comics:
                # Remove duplicates while preserving order
                seen = set()
                unique_comics = []
                for url in comics:
                    if url not in seen:
                        seen.add(url)
                        unique_comics.append(url)

                logger.debug(f"Found {len(unique_comics)} Oglaf comic image(s)")
                return unique_comics

            logger.warning("Could not find Oglaf comic images")
            return []

        except Exception as e:
            logger.error(f"Error extracting Oglaf comic: {e}")
            return []


class WiddershinsExtractor(ComicExtractor):
    """
    Widdershins extractor - scrapes comic page for image.
    """

    def extract_image_urls(self):
        """Extract Widdershins comic image."""
        # Get comic page URL from RSS description
        description = self.entry.get('description', '')
        match = re.search(r'<a\s+href="([^"]+)">', description)

        if not match:
            # Try direct link
            comic_page_url = self.entry.get('link')
        else:
            comic_page_url = match.group(1)

        if not comic_page_url:
            logger.warning("Could not find Widdershins comic page URL")
            return []

        try:
            # Fetch comic page
            response = fetch_url(comic_page_url, session=self.session)
            html_content = response.text

            # Look for pattern: widdershinscomic.com/comics/TIMESTAMP-NUMBER.png
            match = re.search(r'(https?://(?:www\.)?widdershinscomic\.com/comics/\d+-\d+\.png)', html_content)

            if match:
                image_url = match.group(1)
                logger.debug(f"Found Widdershins image: {image_url}")
                return [image_url]

            # Fallback: look for any image in /comics/ directory
            match = re.search(r'(?:src|href)="(https?://(?:www\.)?widdershinscomic\.com/comics/[^"]+\.png)"', html_content)
            if match:
                image_url = match.group(1)
                logger.debug(f"Found Widdershins image (fallback): {image_url}")
                return [image_url]

            logger.warning("Could not find Widdershins comic image")
            return []

        except Exception as e:
            logger.error(f"Error extracting Widdershins comic: {e}")
            return []


class GunnerkriggExtractor(ComicExtractor):
    """
    Gunnerkrigg Court extractor - scrapes comic page for image.
    """

    def extract_image_urls(self):
        """Extract Gunnerkrigg Court comic image."""
        comic_page_url = self.entry.get('link')

        if not comic_page_url:
            logger.warning("No link found for Gunnerkrigg Court")
            return []

        try:
            # Fetch comic page
            response = fetch_url(comic_page_url, session=self.session)
            html_content = response.text

            # Find comic image
            img_match = re.search(r'<img\s+class="comic_image"[^>]*src="([^"]+)"', html_content)

            if not img_match:
                logger.warning("Could not find Gunnerkrigg Court comic image")
                return []

            image_url = img_match.group(1)

            # Handle relative URLs
            if not image_url.startswith('http'):
                image_url = "http://www.gunnerkrigg.com" + image_url

            logger.debug(f"Found Gunnerkrigg Court image: {image_url}")
            return [image_url]

        except Exception as e:
            logger.error(f"Error extracting Gunnerkrigg Court comic: {e}")
            return []


class SavestateExtractor(ComicExtractor):
    """
    Savestate extractor - uses default extraction but removes dimension suffixes.
    """

    def extract_image_urls(self):
        """Extract Savestate comic image and clean URL."""
        content = self.entry.get('content') or self.entry.get('description', '')

        if not content:
            logger.warning(f"No content found for {self.feed_name}")
            return []

        # Look for img tag (specific pattern from reference)
        match = re.search(r'<p><a\s+href[^>]*<img[^>]*src="([^"]+)"', content)

        if not match:
            # Fallback to standard img pattern
            match = re.search(r'<img\s+[^>]*src="([^"]+)"', content)

        if match:
            image_url = match.group(1)

            # Remove dimension suffix (e.g., -300x200)
            image_url = re.sub(r'-\d+x\d+', '', image_url)

            logger.debug(f"Found Savestate image: {image_url}")
            return [image_url]

        logger.warning("No image found for Savestate")
        return []


class WondermarkExtractor(ComicExtractor):
    """
    Wondermark extractor - pattern: wondermark.com/wp-content/uploads/YYYY/MM/YYYY-MM-DD-####xxxx.png
    """

    def extract_image_urls(self):
        """Extract Wondermark comic image."""
        comic_page_url = self.entry.get('link')

        if not comic_page_url:
            logger.warning("No link found for Wondermark")
            return []

        try:
            # Fetch comic page
            response = fetch_url(comic_page_url, session=self.session)
            html_content = response.text

            # Look for pattern: wp-content/uploads/YYYY/MM/YYYY-MM-DD-####xxxx.png
            match = re.search(r'(https?://wondermark\.com/wp-content/uploads/\d{4}/\d{2}/\d{4}-\d{2}-\d{2}-\d+[a-z]+\.png)', html_content)

            if match:
                image_url = match.group(1)
                logger.debug(f"Found Wondermark image: {image_url}")
                return [image_url]

            # Fallback: any image in wp-content/uploads
            match = re.search(r'(https?://wondermark\.com/wp-content/uploads/[^"]+\.png)', html_content)
            if match:
                image_url = match.group(1)
                logger.debug(f"Found Wondermark image (fallback): {image_url}")
                return [image_url]

            logger.warning("No image found for Wondermark")
            return []

        except Exception as e:
            logger.error(f"Error extracting Wondermark comic: {e}")
            return []


class EvilIncExtractor(ComicExtractor):
    """
    Evil Inc extractor - looks for composite .jpg file.
    Pattern: /wp-content/uploads/YYYY/MM/YYYYMMDD_evil.jpg (composite of all panels)
    Note: Individual panels are YYYYMMDD_evil01.png through evil06.png, but we want the composite
    """

    def extract_image_urls(self):
        """Extract Evil Inc composite comic image."""
        comic_page_url = self.entry.get('link')

        if not comic_page_url:
            logger.warning("No link found for Evil Inc")
            return []

        try:
            # Fetch comic page
            response = fetch_url(comic_page_url, session=self.session)
            html_content = response.text

            # Look for the composite image: YYYYMMDD_evil.jpg (NOT evil01-06.png)
            # This is a full composite of all panels
            match = re.search(r'(https?://[^"]*wp-content/uploads/\d{4}/\d{2}/\d{8}_evil\.jpg)', html_content)

            if match:
                image_url = match.group(1)
                logger.debug(f"Found Evil Inc composite image: {image_url}")
                return [image_url]

            # Fallback: try without full URL
            match = re.search(r'wp-content/uploads/(\d{4}/\d{2}/\d{8}_evil\.jpg)', html_content)
            if match:
                image_url = f"https://www.evil-inc.com/wp-content/uploads/{match.group(1)}"
                logger.debug(f"Found Evil Inc composite image (relative): {image_url}")
                return [image_url]

            logger.warning("Could not find Evil Inc composite comic image")
            return []

        except Exception as e:
            logger.error(f"Error extracting Evil Inc comic: {e}")
            return []


class IncaseExtractor(ComicExtractor):
    """
    Incase extractor - pattern: buttsmithy.com/wp-content/uploads/YYYY/MM/FILENAME.jpg
    Filename varies but is sequential (e.g., OG-10.jpg, OG-11.jpg)
    """

    def extract_image_urls(self):
        """Extract Incase comic image."""
        comic_page_url = self.entry.get('link')

        if not comic_page_url:
            logger.warning("No link found for Incase")
            return []

        try:
            # Fetch comic page
            response = fetch_url(comic_page_url, session=self.session)
            html_content = response.text

            # Look for pattern: buttsmithy.com/wp-content/uploads/YYYY/MM/*.jpg
            match = re.search(r'(https?://incase\.buttsmithy\.com/wp-content/uploads/\d{4}/\d{2}/[^"]+\.jpg)', html_content)

            if match:
                image_url = match.group(1)
                logger.debug(f"Found Incase image: {image_url}")
                return [image_url]

            # Fallback: any jpg in wp-content/uploads
            match = re.search(r'(https?://incase\.buttsmithy\.com/wp-content/uploads/[^"]+\.jpg)', html_content)
            if match:
                image_url = match.group(1)
                logger.debug(f"Found Incase image (fallback): {image_url}")
                return [image_url]

            logger.warning("No image found for Incase")
            return []

        except Exception as e:
            logger.error(f"Error extracting Incase comic: {e}")
            return []


def get_extractor(feed_data, session=None, use_vision=True):
    """
    Factory function to get appropriate extractor for a feed.

    Args:
        feed_data: Feed data dict with 'special_handler' field
        session: HTTP session
        use_vision: Whether to use vision model for Oglaf

    Returns:
        ComicExtractor instance
    """
    special_handler = feed_data.get('special_handler')

    extractors = {
        'penny_arcade': PennyArcadeExtractor,
        'oglaf': lambda fd, s: OglafExtractor(fd, s, use_vision=use_vision),
        'widdershins': WiddershinsExtractor,
        'gunnerkrigg': GunnerkriggExtractor,
        'savestate': SavestateExtractor,
        'wondermark': WondermarkExtractor,
        'evil_inc': EvilIncExtractor,
        'incase': IncaseExtractor,
    }

    if special_handler in extractors:
        extractor_class = extractors[special_handler]
        if callable(extractor_class) and special_handler == 'oglaf':
            return extractor_class(feed_data, session)
        else:
            return extractor_class(feed_data, session)

    # Default extractor
    return DefaultExtractor(feed_data, session)
