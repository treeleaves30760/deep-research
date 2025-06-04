import re
from typing import Dict, Any, Optional

from .web_content import WebContent
from .content_quality import ContentQualityChecker
from .content_summarizer import ContentSummarizer


class ContentProcessor:
    """Class for processing web content."""

    def __init__(self, llm_client: Optional[Any] = None):
        """
        Initialize the ContentProcessor.

        Args:
            llm_client: Optional LLM client for content summarization
        """
        self.quality_checker = ContentQualityChecker()
        self.summarizer = ContentSummarizer(llm_client) if llm_client else None

    def process_content(
        self,
        url: str,
        raw_content: str,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        generate_summary: bool = False,
        summary_type: str = "concise"
    ) -> WebContent:
        """
        Process raw web content and create a WebContent object.

        Args:
            url: Source URL
            raw_content: Raw HTML content
            title: Optional title
            metadata: Optional metadata dictionary
            generate_summary: Whether to generate a summary
            summary_type: Type of summary to generate

        Returns:
            Processed WebContent object
        """
        # Clean and extract main content
        cleaned_content = self._clean_text(raw_content)
        main_content = self._extract_main_content(raw_content)

        # Convert to markdown
        markdown_content = self._html_to_markdown(main_content)

        # Create WebContent object
        content = WebContent(
            url=url,
            content=cleaned_content,
            title=title or self._extract_title(raw_content),
            metadata=metadata or self._extract_metadata(raw_content)
        )
        content.markdown = markdown_content

        # Check content quality
        quality_metrics = self.quality_checker.check_quality(content)
        content.quality_metrics = quality_metrics

        # Generate summary if requested
        if generate_summary and self.summarizer:
            summary = self.summarizer.summarize_content(
                content.content,
                summary_type=summary_type
            )
            content.update_summary(summary, summary_type)

        return content

    def _clean_text(self, text: str) -> str:
        """
        Clean raw text content.

        Args:
            text: Raw text to clean

        Returns:
            Cleaned text
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        # Remove special characters
        text = re.sub(r'[^\w\s.,!?-]', '', text)

        return text.strip()

    def _extract_main_content(self, html: str) -> str:
        """
        Extract main content from HTML.

        Args:
            html: Raw HTML content

        Returns:
            Extracted main content
        """
        # Remove unwanted blocks like script, style, nav, footer and header
        cleaned = re.sub(
            r'<(script|style|nav|footer|header)[^>]*>.*?</\1>',
            '',
            html,
            flags=re.DOTALL | re.IGNORECASE,
        )

        # Prefer content inside <main>, <article> or <body>
        match = re.search(
            r'<(main|article|body)[^>]*>(.*?)</\1>',
            cleaned,
            flags=re.DOTALL | re.IGNORECASE,
        )
        return match.group(2) if match else cleaned

    def _html_to_markdown(self, html: str) -> str:
        """
        Convert HTML to Markdown.

        Args:
            html: HTML content

        Returns:
            Markdown content
        """
        # Very small subset of HTML to Markdown conversion so tests do not rely
        # on external libraries. Only <h1> and <p> tags are handled.
        text = re.sub(
            r'<h1[^>]*>(.*?)</h1>',
            lambda m: '# ' + m.group(1).strip() + '\n\n',
            html,
            flags=re.DOTALL | re.IGNORECASE,
        )
        text = re.sub(
            r'<p[^>]*>(.*?)</p>',
            lambda m: m.group(1).strip() + '\n\n',
            text,
            flags=re.DOTALL | re.IGNORECASE,
        )
        # Remove any remaining tags
        text = re.sub(r'<[^>]+>', '', text)
        return text.strip()

    def _extract_title(self, html: str) -> str:
        """
        Extract title from HTML.

        Args:
            html: Raw HTML content

        Returns:
            Extracted title
        """
        match = re.search(
            r'<title[^>]*>(.*?)</title>',
            html,
            flags=re.DOTALL | re.IGNORECASE,
        )
        return match.group(1).strip() if match else ""

    def _extract_metadata(self, html: str) -> Dict[str, Any]:
        """
        Extract metadata from HTML.

        Args:
            html: Raw HTML content

        Returns:
            Dictionary of metadata
        """
        metadata: Dict[str, Any] = {}
        for name, content in re.findall(
            r'<meta[^>]+?(?:name|property)=["\']([^"\']+)["\'][^>]*?content=["\']([^"\']+)["\'][^>]*?>',
            html,
            flags=re.IGNORECASE,
        ):
            metadata[name] = content

        return metadata
