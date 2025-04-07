import unittest
from unittest.mock import Mock, patch
from src.content_processing.content_summarizer import ContentSummarizer


class TestContentSummarizer(unittest.TestCase):
    """Test cases for the ContentSummarizer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_llm_client = Mock()
        self.summarizer = ContentSummarizer(llm_client=self.mock_llm_client)

    def test_initialization(self):
        """Test the initialization of ContentSummarizer."""
        # Test with LLM client
        summarizer_with_llm = ContentSummarizer(
            llm_client=self.mock_llm_client)
        self.assertIsNotNone(summarizer_with_llm.llm_client)

        # Test without LLM client
        with self.assertRaises(ValueError):
            ContentSummarizer()

    def test_summarize_content(self):
        """Test summarizing content."""
        # Test data
        content = """
        This is a long article about artificial intelligence.
        It discusses various machine learning algorithms.
        It explains how neural networks work.
        It covers deep learning applications.
        It concludes with future predictions.
        """

        # Mock LLM client responses
        self.mock_llm_client.generate_summary.side_effect = [
            "Summary of first part.",
            "Summary of second part.",
            "Final combined summary."
        ]

        # Test concise summary
        concise_summary = self.summarizer.summarize_content(
            content,
            summary_type="concise"
        )
        self.assertEqual(concise_summary, "Final combined summary.")

        # Test detailed summary
        detailed_summary = self.summarizer.summarize_content(
            content,
            summary_type="detailed"
        )
        self.assertEqual(detailed_summary, "Final combined summary.")

        # Test key points summary
        key_points_summary = self.summarizer.summarize_content(
            content,
            summary_type="key_points"
        )
        self.assertEqual(key_points_summary, "Final combined summary.")

        # Test invalid summary type
        with self.assertRaises(ValueError):
            self.summarizer.summarize_content(content, summary_type="invalid")

    def test_chunk_content(self):
        """Test chunking content."""
        # Test data
        content = "This is a test content. " * 100  # Create a long content

        # Chunk content
        chunks = self.summarizer._chunk_content(content)

        # Check if content is chunked correctly
        self.assertGreater(len(chunks), 1)  # Should have multiple chunks
        for chunk in chunks:
            self.assertLessEqual(len(chunk), self.summarizer.max_chunk_size)

    def test_combine_summaries(self):
        """Test combining summaries."""
        # Test data
        summaries = [
            "First part summary.",
            "Second part summary.",
            "Third part summary."
        ]

        # Mock LLM client response
        self.mock_llm_client.generate_summary.return_value = "Combined summary of all parts."

        # Combine summaries
        combined_summary = self.summarizer._combine_summaries(summaries)

        # Check if summaries are combined correctly
        self.assertEqual(combined_summary, "Combined summary of all parts.")

        # Test with empty summaries
        with self.assertRaises(ValueError):
            self.summarizer._combine_summaries([])

    def test_get_summary_prompt(self):
        """Test getting summary prompt."""
        # Test concise summary prompt
        concise_prompt = self.summarizer._get_summary_prompt("concise")
        self.assertIn("concise", concise_prompt.lower())

        # Test detailed summary prompt
        detailed_prompt = self.summarizer._get_summary_prompt("detailed")
        self.assertIn("detailed", detailed_prompt.lower())

        # Test key points summary prompt
        key_points_prompt = self.summarizer._get_summary_prompt("key_points")
        self.assertIn("key points", key_points_prompt.lower())

        # Test invalid summary type
        with self.assertRaises(ValueError):
            self.summarizer._get_summary_prompt("invalid")


if __name__ == "__main__":
    unittest.main()
