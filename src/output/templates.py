"""
HTML templates for RSS Feed Processor
"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - {date}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
            padding: 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}

        header {{
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 3px solid #007bff;
        }}

        h1 {{
            color: #007bff;
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        .date {{
            color: #666;
            font-size: 1.2em;
        }}

        .summary {{
            background-color: #e9ecef;
            padding: 20px;
            border-radius: 6px;
            margin-bottom: 30px;
        }}

        .summary h2 {{
            color: #495057;
            font-size: 1.3em;
            margin-bottom: 10px;
        }}

        .summary-stats {{
            display: flex;
            gap: 30px;
            flex-wrap: wrap;
        }}

        .stat {{
            font-size: 1.1em;
        }}

        .stat strong {{
            color: #007bff;
        }}

        section {{
            margin-bottom: 40px;
        }}

        section h2 {{
            color: #495057;
            font-size: 2em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #dee2e6;
        }}

        details {{
            margin-bottom: 20px;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            overflow: hidden;
        }}

        summary {{
            padding: 15px 20px;
            background-color: #f8f9fa;
            cursor: pointer;
            font-weight: 600;
            font-size: 1.1em;
            user-select: none;
            transition: background-color 0.2s;
        }}

        summary:hover {{
            background-color: #e9ecef;
        }}

        details[open] summary {{
            background-color: #007bff;
            color: white;
        }}

        .feed-details {{
            margin-bottom: 15px;
        }}

        .feed-summary {{
            padding: 12px 20px;
            font-size: 1.05em;
        }}

        .feed-content {{
            padding: 15px 20px;
        }}

        .content {{
            padding: 20px;
        }}

        .comic {{
            margin-bottom: 30px;
        }}

        .comic-title {{
            font-size: 1.2em;
            color: #007bff;
            margin-bottom: 10px;
            font-weight: 600;
        }}

        .comic-images {{
            display: flex;
            flex-direction: column;
            gap: 15px;
            margin-top: 15px;
        }}

        .comic-image {{
            max-width: 100%;
            height: auto;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }}

        .comic-link {{
            display: inline-block;
            margin-top: 10px;
            color: #007bff;
            text-decoration: none;
        }}

        .comic-link:hover {{
            text-decoration: underline;
        }}

        .article {{
            margin-bottom: 25px;
            padding-bottom: 25px;
            border-bottom: 1px solid #dee2e6;
        }}

        .article:last-child {{
            border-bottom: none;
        }}

        .article-header {{
            margin-bottom: 15px;
        }}

        .article-title {{
            font-size: 1.3em;
            color: #212529;
            margin-bottom: 5px;
        }}

        .article-meta {{
            color: #6c757d;
            font-size: 0.9em;
            margin-bottom: 10px;
        }}

        .article-summary {{
            color: #495057;
            line-height: 1.8;
            margin-bottom: 10px;
        }}

        .article-link {{
            display: inline-block;
            color: #007bff;
            text-decoration: none;
            font-weight: 500;
        }}

        .article-link:hover {{
            text-decoration: underline;
        }}

        .article.clickbait {{
            background-color: #fff3cd;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #ffc107;
        }}

        .clickbait-badge {{
            display: inline-block;
            background-color: #ffc107;
            color: #000;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 0.8em;
            font-weight: 600;
            margin-left: 10px;
        }}

        .error {{
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 15px;
        }}

        .error-feed {{
            font-weight: 600;
            margin-bottom: 5px;
        }}

        .error-message {{
            font-family: monospace;
            font-size: 0.9em;
        }}

        footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #dee2e6;
            text-align: center;
            color: #6c757d;
            font-size: 0.9em;
        }}

        /* Dark mode support */
        @media (prefers-color-scheme: dark) {{
            body {{
                color: #e4e4e4;
                background-color: #1a1a1a;
            }}

            .container {{
                background-color: #2d2d2d;
                box-shadow: 0 2px 10px rgba(0,0,0,0.5);
            }}

            header {{
                border-bottom: 3px solid #4a9eff;
            }}

            h1 {{
                color: #4a9eff;
            }}

            .date {{
                color: #b0b0b0;
            }}

            .summary {{
                background-color: #383838;
            }}

            .summary h2 {{
                color: #e4e4e4;
            }}

            .stat strong {{
                color: #4a9eff;
            }}

            section h2 {{
                color: #e4e4e4;
                border-bottom: 2px solid #484848;
            }}

            details {{
                border: 1px solid #484848;
            }}

            summary {{
                background-color: #383838;
                color: #e4e4e4;
            }}

            summary:hover {{
                background-color: #404040;
            }}

            details[open] summary {{
                background-color: #4a9eff;
                color: #1a1a1a;
            }}

            .comic-title {{
                color: #4a9eff;
            }}

            .comic-image {{
                box-shadow: 0 2px 8px rgba(0,0,0,0.5);
            }}

            .comic-link {{
                color: #5eb3ff;
            }}

            .article {{
                border-bottom: 1px solid #484848;
            }}

            .article-title {{
                color: #e4e4e4;
            }}

            .article-meta {{
                color: #a0a0a0;
            }}

            .article-summary {{
                color: #c8c8c8;
            }}

            .article-link {{
                color: #5eb3ff;
            }}

            /* Clickbait styling for dark mode */
            .article.clickbait {{
                background-color: #3d3416;
                border-left: 4px solid #d4a017;
            }}

            .clickbait-badge {{
                background-color: #d4a017;
                color: #1a1a1a;
            }}

            /* Error styling for dark mode */
            .error {{
                background-color: #3d1f1f;
                border: 1px solid #5a2a2a;
                color: #f5a9a9;
            }}

            footer {{
                border-top: 2px solid #484848;
                color: #a0a0a0;
            }}

            footer p {{
                color: #c8c8c8;
            }}

            footer a {{
                color: #5eb3ff;
            }}

            footer a:hover {{
                color: #4a9eff;
            }}
        }}

        @media (max-width: 768px) {{
            body {{
                padding: 10px;
            }}

            .container {{
                padding: 20px;
            }}

            h1 {{
                font-size: 2em;
            }}

            .summary-stats {{
                flex-direction: column;
                gap: 10px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{title}</h1>
            <div class="date">{date}</div>
        </header>

        <div class="summary">
            <h2>Summary</h2>
            <div class="summary-stats">
                <div class="stat"><strong>{comics_count}</strong> Comics</div>
                <div class="stat"><strong>{articles_count}</strong> Articles</div>
                <div class="stat"><strong>{errors_count}</strong> Errors</div>
            </div>
        </div>

        {comics_section}

        {articles_section}

        {errors_section}

        <footer>
            <p>Generated on {datetime} by <a href="https://github.com/Alexthestampede/DailyFeedSanity" target="_blank" style="color: #007bff; text-decoration: none;">DailyFeedSanity</a></p>
            <p style="margin-top: 10px; font-size: 0.95em;">A project made possible by <a href="https://claude.ai/code" target="_blank" style="color: #007bff; text-decoration: none;">Claude Code</a></p>
            <p style="margin-top: 15px; font-size: 1em; color: #495057;">
                Please consider visiting the original sites and supporting the creators who make this content possible.
                If you enjoy a comic or article, click through to the source and show your appreciation!
            </p>
        </footer>
    </div>
</body>
</html>
"""

COMICS_SECTION_TEMPLATE = """
<section id="comics">
    <h2>Webcomics ({count} total)</h2>
    <div class="content">
        {comics_html}
    </div>
</section>
"""

COMIC_ITEM_TEMPLATE = """
<details open class="feed-details">
    <summary class="feed-summary">{name}</summary>
    <div class="comic">
        <div class="comic-images">
            {images_html}
        </div>
        <a href="{link}" class="comic-link" target="_blank">View original</a>
    </div>
</details>
"""

ARTICLES_SECTION_TEMPLATE = """
<section id="articles">
    <h2>News Articles ({count} total)</h2>
    <div class="content">
        {articles_html}
    </div>
</section>
"""

ARTICLE_ITEM_TEMPLATE = """
<div class="article{clickbait_class}">
    <div class="article-header">
        <div class="article-title">
            {title}{clickbait_badge}
        </div>
        <div class="article-meta">
            Source: {feed_name} | {date}
            {author_info}
        </div>
    </div>
    <div class="article-summary">{summary}</div>
    <a href="{url}" class="article-link" target="_blank">Read full article</a>
</div>
"""

ERRORS_SECTION_TEMPLATE = """
<section id="errors">
    <h2>Errors</h2>
    <details>
        <summary>Click to view errors ({count} total)</summary>
        <div class="content">
            {errors_html}
        </div>
    </details>
</section>
"""

ERROR_ITEM_TEMPLATE = """
<div class="error">
    <div class="error-feed">Feed: {feed_url}</div>
    <div class="error-message">{error_message}</div>
</div>
"""
