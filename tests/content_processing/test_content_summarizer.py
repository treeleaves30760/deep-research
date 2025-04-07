import unittest
from unittest.mock import Mock, patch
from src.content_processing.content_summarizer import ContentSummarizer


class TestContentSummarizer(unittest.TestCase):
    """Test cases for the ContentSummarizer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_llm = Mock()
        self.summarizer = ContentSummarizer(self.mock_llm)

        # Sample content for testing
        self.sample_content = """
        This is a test content with multiple paragraphs.
        
        It contains various topics and ideas that need to be summarized.
        
        The content is structured with proper paragraphs and formatting.
        
        In conclusion, this is a good test content for summarization.
        """

    def test_initialization(self):
        """Test the initialization of ContentSummarizer."""
        # Test with LLM client
        summarizer = ContentSummarizer(self.mock_llm)
        self.assertIsNotNone(summarizer.llm_client)

        # Test without LLM client
        with self.assertRaises(ValueError):
            ContentSummarizer(None)

    def test_chunk_content(self):
        """Test chunking content."""
        # Test with short content
        chunks = self.summarizer._chunk_content("Short content")
        self.assertEqual(len(chunks), 1)

        # Test with long content
        # Create content with many paragraphs that will exceed max_chunk_size
        long_content = ""
        for i in range(1000):
            long_content += f"This is paragraph {i} with some additional text to make it longer. " * 10 + "\n\n"

        chunks = self.summarizer._chunk_content(long_content)
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertLessEqual(len(chunk.split()),
                                 self.summarizer.max_chunk_size)

    def test_summarize_content(self):
        """Test summarizing content."""
        # Set a consistent return value for all summary types
        self.mock_llm.generate_summary.return_value = "Summary of first part."

        # Test concise summary
        concise_summary = self.summarizer.summarize_content(
            self.sample_content,
            summary_type="concise"
        )
        self.assertEqual(concise_summary, "Summary of first part.")

        # Test detailed summary
        detailed_summary = self.summarizer.summarize_content(
            self.sample_content,
            summary_type="detailed"
        )
        self.assertEqual(detailed_summary, "Summary of first part.")

        # Test key points summary
        key_points = self.summarizer.summarize_content(
            self.sample_content,
            summary_type="key_points"
        )
        self.assertEqual(key_points, "Summary of first part.")

    def test_combine_summaries(self):
        """Test combining summaries."""
        summaries = ["First summary.", "Second summary.", "Third summary."]
        self.mock_llm.generate_summary.return_value = "Final combined summary."
        combined = self.summarizer._combine_summaries(summaries)
        self.assertEqual(combined, "Final combined summary.")

    def test_invalid_summary_type(self):
        """Test handling invalid summary type."""
        with self.assertRaises(ValueError):
            self.summarizer.summarize_content(
                self.sample_content,
                summary_type="invalid"
            )


if __name__ == '__main__':
    unittest.main()
