"""
HTML generator for RSS Feed Processor
"""
import os
from datetime import datetime
from pathlib import Path
from .templates import (
    HTML_TEMPLATE,
    COMICS_SECTION_TEMPLATE,
    COMIC_ITEM_TEMPLATE,
    ARTICLES_SECTION_TEMPLATE,
    ARTICLE_ITEM_TEMPLATE,
    ERRORS_SECTION_TEMPLATE,
    ERROR_ITEM_TEMPLATE
)
from ..utils.logging_config import get_logger
from ..config import HTML_TITLE, DATE_FORMAT, DATETIME_FORMAT

logger = get_logger(__name__)


class HTMLGenerator:
    """
    Generate HTML output from processing results.
    """

    def __init__(self):
        """
        Initialize HTML generator.
        """
        pass

    def generate(self, processing_results, comic_results, article_results, output_dir):
        """
        Generate HTML page from processing results.

        Args:
            processing_results: ProcessingResults object from feed manager
            comic_results: List of comic download results
            article_results: List of article processing results
            output_dir: Directory to save HTML file

        Returns:
            Path to generated HTML file
        """
        logger.info("Generating HTML output")

        try:
            # Prepare data
            date_str = datetime.now().strftime(DATE_FORMAT)
            datetime_str = datetime.now().strftime(DATETIME_FORMAT)

            # Generate sections
            comics_html = self._generate_comics_section(comic_results, output_dir)
            articles_html = self._generate_articles_section(article_results)
            errors_html = self._generate_errors_section(processing_results.errors)

            # Count successes
            comics_count = sum(1 for r in comic_results if r.get('success', False))
            articles_count = sum(1 for r in article_results if r.get('success', False))
            errors_count = len(processing_results.errors)

            # Generate final HTML
            html = HTML_TEMPLATE.format(
                title=HTML_TITLE,
                date=date_str,
                datetime=datetime_str,
                comics_count=comics_count,
                articles_count=articles_count,
                errors_count=errors_count,
                comics_section=comics_html,
                articles_section=articles_html,
                errors_section=errors_html
            )

            # Save to file
            output_path = Path(output_dir) / "index.html"
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)

            logger.info(f"Generated HTML file: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"Error generating HTML: {e}")
            raise

    def _generate_comics_section(self, comic_results, output_dir):
        """
        Generate comics section HTML.

        Args:
            comic_results: List of comic download results
            output_dir: Output directory for relative paths

        Returns:
            HTML string
        """
        if not comic_results:
            return ""

        # Filter successful comics
        successful_comics = [r for r in comic_results if r.get('success', False)]

        if not successful_comics:
            return ""

        # Generate comic items
        comics_html_list = []

        for comic in successful_comics:
            comic_html = self._generate_comic_item(comic, output_dir)
            comics_html_list.append(comic_html)

        comics_html = '\n'.join(comics_html_list)

        # Wrap in section
        section_html = COMICS_SECTION_TEMPLATE.format(
            count=len(successful_comics),
            comics_html=comics_html
        )

        return section_html

    def _generate_comic_item(self, comic, output_dir):
        """
        Generate HTML for a single comic.

        Args:
            comic: Comic result dict
            output_dir: Output directory for relative paths

        Returns:
            HTML string
        """
        comic_info = comic.get('comic_info', {})
        name = comic.get('feed_name', 'Unknown')
        link = comic_info.get('link', '#')
        images = comic.get('images', [])

        # Generate image tags
        images_html_list = []
        for image_path in images:
            # Convert to relative path
            rel_path = os.path.relpath(image_path, output_dir)
            img_html = f'<img src="{rel_path}" alt="{name}" class="comic-image">'
            images_html_list.append(img_html)

        images_html = '\n'.join(images_html_list)

        # Generate comic HTML
        comic_html = COMIC_ITEM_TEMPLATE.format(
            name=name,
            images_html=images_html,
            link=link
        )

        return comic_html

    def _generate_articles_section(self, article_results):
        """
        Generate articles section HTML.

        Args:
            article_results: List of article processing results

        Returns:
            HTML string
        """
        if not article_results:
            return ""

        # Filter successful articles
        successful_articles = [r for r in article_results if r.get('success', False)]

        if not successful_articles:
            return ""

        # Group articles by feed name
        from collections import defaultdict
        articles_by_feed = defaultdict(list)
        for article in successful_articles:
            feed_name = article.get('feed_name', 'Unknown')
            articles_by_feed[feed_name].append(article)

        # Generate feed groups
        feed_groups_html_list = []

        for feed_name in sorted(articles_by_feed.keys()):
            articles = articles_by_feed[feed_name]

            # Generate article items for this feed
            articles_html_list = []
            for article in articles:
                article_html = self._generate_article_item(article)
                articles_html_list.append(article_html)

            articles_html = '\n'.join(articles_html_list)

            # Wrap in collapsible feed section
            feed_html = f'''
<details open class="feed-details">
    <summary class="feed-summary">{self._escape_html(feed_name)} ({len(articles)} article{"s" if len(articles) > 1 else ""})</summary>
    <div class="feed-content">
        {articles_html}
    </div>
</details>
'''
            feed_groups_html_list.append(feed_html)

        articles_html = '\n'.join(feed_groups_html_list)

        # Wrap in section
        section_html = ARTICLES_SECTION_TEMPLATE.format(
            count=len(successful_articles),
            articles_html=articles_html
        )

        return section_html

    def _generate_article_item(self, article):
        """
        Generate HTML for a single article.

        Args:
            article: Article result dict

        Returns:
            HTML string
        """
        feed_name = article.get('feed_name', 'Unknown')
        title = article.get('generated_title', article.get('original_title', 'Untitled'))
        summary = article.get('summary', '')
        url = article.get('url', '#')
        author = article.get('author')
        date = article.get('date', '')
        is_clickbait = article.get('is_clickbait', False)
        clickbait_detected_by = article.get('clickbait_detected_by')

        # Format date
        if isinstance(date, datetime):
            date_str = date.strftime(DATE_FORMAT)
        else:
            date_str = str(date) if date else 'Unknown date'

        # Author info
        author_info = f"| Author: {author}" if author else ""

        # Clickbait styling with detection source
        clickbait_class = " clickbait" if is_clickbait else ""
        if is_clickbait:
            if clickbait_detected_by == "both":
                badge_text = "CLICKBAIT (AI + Author)"
            elif clickbait_detected_by == "ollama":
                badge_text = "CLICKBAIT (AI Detected)"
            elif clickbait_detected_by == "author":
                badge_text = "CLICKBAIT (Known Author)"
            else:
                badge_text = "CLICKBAIT"
            clickbait_badge = f'<span class="clickbait-badge">{badge_text}</span>'
        else:
            clickbait_badge = ""

        # Generate article HTML
        article_html = ARTICLE_ITEM_TEMPLATE.format(
            title=self._escape_html(title),
            feed_name=self._escape_html(feed_name),
            date=date_str,
            author_info=author_info,
            summary=self._escape_html(summary),
            url=url,
            clickbait_class=clickbait_class,
            clickbait_badge=clickbait_badge
        )

        return article_html

    def _generate_errors_section(self, errors):
        """
        Generate errors section HTML.

        Args:
            errors: List of error dicts

        Returns:
            HTML string
        """
        if not errors:
            return ""

        # Generate error items
        errors_html_list = []

        for error in errors:
            error_html = self._generate_error_item(error)
            errors_html_list.append(error_html)

        errors_html = '\n'.join(errors_html_list)

        # Wrap in section
        section_html = ERRORS_SECTION_TEMPLATE.format(
            count=len(errors),
            errors_html=errors_html
        )

        return section_html

    def _generate_error_item(self, error):
        """
        Generate HTML for a single error.

        Args:
            error: Error dict

        Returns:
            HTML string
        """
        feed_url = error.get('feed_url', 'Unknown')
        error_message = error.get('error', 'Unknown error')

        error_html = ERROR_ITEM_TEMPLATE.format(
            feed_url=self._escape_html(feed_url),
            error_message=self._escape_html(error_message)
        )

        return error_html

    def _escape_html(self, text):
        """
        Escape HTML special characters.

        Args:
            text: Text to escape

        Returns:
            Escaped text
        """
        if not text:
            return ""

        text = str(text)
        replacements = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;'
        }

        for char, escaped in replacements.items():
            text = text.replace(char, escaped)

        return text
