import unittest
from unittest.mock import Mock, patch
from datetime import datetime
from src.content_processing.content_processor import ContentProcessor
from src.content_processing.web_content import WebContent


class TestContentProcessor(unittest.TestCase):
    """Test cases for the ContentProcessor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.processor = ContentProcessor()

        # Sample HTML content for testing
        self.sample_html = """
        <html>
            <head>
                <title>Test Page</title>
                <meta name="author" content="Test Author">
                <meta name="description" content="Test Description">
            </head>
            <body>
                <main>
                    <h1>Test Title</h1>
                    <p>This is a test paragraph.</p>
                    <p>This is another paragraph.</p>
                </main>
            </body>
        </html>
        """

    def test_process_content_basic(self):
        """Test basic content processing."""
        content = self.processor.process_content(
            url="https://example.com",
            raw_content=self.sample_html
        )

        # Check that content is processed correctly
        self.assertIsInstance(content, WebContent)
        self.assertEqual(content.url, "https://example.com")
        self.assertIn("Test Title", content.content)
        self.assertIn("test paragraph", content.content)

        # Check metadata
        self.assertIn("author", content.metadata)
        self.assertEqual(content.metadata["author"], "Test Author")

    def test_process_content_with_title_and_metadata(self):
        """Test content processing with custom title and metadata."""
        custom_title = "Custom Title"
        custom_metadata = {"source": "test"}

        content = self.processor.process_content(
            url="https://example.com",
            raw_content=self.sample_html,
            title=custom_title,
            metadata=custom_metadata
        )

        self.assertEqual(content.title, custom_title)
        self.assertEqual(content.metadata["source"], "test")

    def test_clean_text(self):
        """Test text cleaning."""
        dirty_text = """
        <p>This is a <b>dirty</b> text with
        extra whitespace and <script>JavaScript</script>.</p>
        """

        clean_text = self.processor._clean_text(dirty_text)

        self.assertNotIn("<b>", clean_text)
        self.assertNotIn("<script>", clean_text)
        self.assertNotIn("  ", clean_text)  # No double spaces

    def test_extract_main_content(self):
        """Test main content extraction."""
        html = """
        <html>
            <body>
                <nav>Navigation</nav>
                <main>
                    <article>
                        <h1>Main Content</h1>
                        <p>Important text</p>
                    </article>
                </main>
                <footer>Footer</footer>
            </body>
        </html>
        """

        content = self.processor._extract_main_content(html)

        self.assertIn("Main Content", content)
        self.assertIn("Important text", content)
        self.assertNotIn("Navigation", content)
        self.assertNotIn("Footer", content)

    def test_html_to_markdown(self):
        """Test HTML to Markdown conversion."""
        html = "<h1>Title</h1><p>Paragraph</p>"
        markdown = self.processor._html_to_markdown(html)

        # The markdown library might produce different output formats
        # So we'll check for the content rather than the exact format
        self.assertIn("Title", markdown)
        self.assertIn("Paragraph", markdown)

    def test_extract_title(self):
        """Test title extraction."""
        title = self.processor._extract_title(self.sample_html)
        self.assertEqual(title, "Test Page")

    def test_extract_metadata(self):
        """Test metadata extraction."""
        metadata = self.processor._extract_metadata(self.sample_html)

        self.assertIn("author", metadata)
        self.assertIn("description", metadata)
        self.assertEqual(metadata["author"], "Test Author")
        self.assertEqual(metadata["description"], "Test Description")

    def test_process_content_with_summary(self):
        """Test content processing with summary generation."""
        # Create a mock LLM client
        mock_llm = Mock()
        mock_llm.generate_summary.return_value = "Test summary"

        # Create a processor with the mock LLM client
        processor = ContentProcessor(llm_client=mock_llm)

        # Process content with summary generation
        content = processor.process_content(
            url="https://example.com",
            raw_content=self.sample_html,
            generate_summary=True
        )

        # Verify that the summary was generated
        self.assertEqual(content.summary, "Test summary")
        self.assertEqual(content.summary_type, "concise")

        # Verify that the LLM client was called
        mock_llm.generate_summary.assert_called_once()


if __name__ == '__main__':
    unittest.main()
