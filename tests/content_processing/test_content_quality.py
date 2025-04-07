import unittest
from datetime import datetime, timedelta
from src.content_processing.content_quality import ContentQualityChecker
from src.content_processing.web_content import WebContent


class TestContentQualityChecker(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.checker = ContentQualityChecker()

        # Sample content for testing
        self.sample_text = """
        # Test Title
        
        This is a test paragraph with some content. It has multiple sentences.
        The content is well structured and readable.
        
        Furthermore, this paragraph has transition words and good coherence.
        The sentences are not too long and use simple words.
        
        In conclusion, this is a good test content with proper structure.
        """

        # Create a WebContent object for testing
        self.web_content = WebContent(
            url="https://example.com/test",
            content=self.sample_text,
            title="Test Title",
            timestamp=datetime.now(),
            metadata={
                "author": "Test Author",
                "published_date": "2024-03-20"
            }
        )

    def test_check_quality_with_string(self):
        """Test quality checking with string input."""
        metrics = self.checker.check_quality(self.sample_text)

        # Check that all basic metrics are present
        self.assertIn('completeness', metrics)
        self.assertIn('readability', metrics)
        self.assertIn('coherence', metrics)
        self.assertIn('relevance', metrics)

        # Check that metrics are within expected range
        for metric in metrics.values():
            self.assertGreaterEqual(metric, 0.0)
            self.assertLessEqual(metric, 1.0)

    def test_check_quality_with_webcontent(self):
        """Test quality checking with WebContent input."""
        metrics = self.checker.check_quality(self.web_content)

        # Check that all metrics are present
        self.assertIn('completeness', metrics)
        self.assertIn('readability', metrics)
        self.assertIn('coherence', metrics)
        self.assertIn('relevance', metrics)
        self.assertIn('freshness', metrics)
        self.assertIn('reliability', metrics)
        self.assertIn('uniqueness', metrics)
        self.assertIn('overall_score', metrics)

        # Check that metrics are within expected range
        for metric in metrics.values():
            self.assertGreaterEqual(metric, 0.0)
            self.assertLessEqual(metric, 1.0)

    def test_check_completeness(self):
        """Test completeness checking."""
        # Test with complete content
        score = self.checker._check_completeness(self.sample_text)
        # Should be high for well-structured content
        self.assertGreater(score, 0.7)

        # Test with incomplete content
        incomplete_text = "Short text."
        score = self.checker._check_completeness(incomplete_text)
        self.assertLess(score, 0.5)  # Should be low for incomplete content

    def test_check_readability(self):
        """Test readability checking."""
        # Test with readable content
        score = self.checker._check_readability(self.sample_text)
        self.assertGreater(score, 0.6)  # Should be high for readable content

        # Test with less readable content
        complex_text = "This is a very complex sentence with many difficult words and complicated structures that make it hard to understand for the average reader who might struggle with such sophisticated language."
        score = self.checker._check_readability(complex_text)
        self.assertLess(score, 0.5)  # Should be lower for complex content

    def test_check_coherence(self):
        """Test coherence checking."""
        # Test with coherent content
        score = self.checker._check_coherence(self.sample_text)
        # Should be at least 0.5 for coherent content
        self.assertGreaterEqual(score, 0.5)

        # Test with less coherent content
        incoherent_text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        score = self.checker._check_coherence(incoherent_text)
        self.assertLess(score, 0.5)  # Should be lower for incoherent content

    def test_check_relevance(self):
        """Test relevance checking."""
        # Test with default query (should return default score)
        score = self.checker._check_relevance(self.sample_text)
        self.assertEqual(score, 0.7)

        # Test with matching query
        score = self.checker._check_relevance(self.sample_text, "test content")
        self.assertGreater(score, 0.7)

        # Test with non-matching query
        score = self.checker._check_relevance(
            self.sample_text, "unrelated topic")
        self.assertLess(score, 0.5)

    def test_check_freshness(self):
        """Test freshness checking."""
        # Test with recent content
        score = self.checker._check_freshness(self.web_content)
        self.assertGreater(score, 0.8)  # Should be high for recent content

        # Test with old content
        old_content = WebContent(
            url="https://example.com/old",
            content="Old content",
            timestamp=datetime.now() - timedelta(days=400)
        )
        score = self.checker._check_freshness(old_content)
        self.assertLess(score, 0.5)  # Should be lower for old content

    def test_check_reliability(self):
        """Test reliability checking."""
        # Test with reliable content
        score = self.checker._check_reliability(self.web_content)
        self.assertGreater(score, 0.7)  # Should be high for reliable content

        # Test with less reliable content
        unreliable_content = WebContent(
            url="https://example.com/unreliable",
            content="Unreliable content",
            metadata={}
        )
        score = self.checker._check_reliability(unreliable_content)
        self.assertLess(score, 0.7)  # Should be lower for unreliable content

    def test_check_uniqueness(self):
        """Test uniqueness checking."""
        # Test with unique content
        score = self.checker._check_uniqueness(self.web_content)
        self.assertGreater(score, 0.7)  # Should be high for unique content

        # Test with duplicate content
        duplicate_content = WebContent(
            url="https://example.com/duplicate",
            content="This is a test. This is a test. This is a test."
        )
        score = self.checker._check_uniqueness(duplicate_content)
        self.assertLess(score, 0.5)  # Should be lower for duplicate content

    def test_backward_compatibility(self):
        """Test backward compatibility with check_content_quality method."""
        # Test that check_content_quality is an alias for check_quality
        metrics1 = self.checker.check_quality(self.web_content)
        metrics2 = self.checker.check_content_quality(self.web_content)
        self.assertEqual(metrics1, metrics2)


if __name__ == '__main__':
    unittest.main()
