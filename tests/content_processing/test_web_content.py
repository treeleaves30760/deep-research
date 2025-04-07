import unittest
from datetime import datetime
from src.content_processing.web_content import WebContent


class TestWebContent(unittest.TestCase):
    """Test cases for the WebContent class."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_content = WebContent(
            id="test-id",
            url="https://example.com",
            title="Test Title",
            content="This is a test content.",
            markdown="# Test Title\n\nThis is a test content.",
            metadata={"author": "Test Author", "published_date": "2023-01-01"}
        )

    def test_initialization(self):
        """Test the initialization of WebContent."""
        self.assertEqual(self.test_content.id, "test-id")
        self.assertEqual(self.test_content.url, "https://example.com")
        self.assertEqual(self.test_content.title, "Test Title")
        self.assertEqual(self.test_content.content, "This is a test content.")
        self.assertEqual(self.test_content.markdown,
                         "# Test Title\n\nThis is a test content.")
        self.assertEqual(self.test_content.metadata, {
                         "author": "Test Author", "published_date": "2023-01-01"})
        self.assertIsNone(self.test_content.embeddings)
        self.assertEqual(self.test_content.tags, [])
        self.assertIsNotNone(self.test_content.timestamp)
        self.assertIsNotNone(self.test_content.last_updated)
        self.assertEqual(self.test_content.relevance_score, 0.0)
        self.assertEqual(self.test_content.quality_metrics, {})
        self.assertIsNone(self.test_content.summary)
        self.assertIsNone(self.test_content.summary_type)

    def test_update_content(self):
        """Test updating content and markdown."""
        new_content = "Updated test content."
        new_markdown = "# Test Title\n\nUpdated test content."

        # Store the original last_updated
        original_last_updated = self.test_content.last_updated

        # Update content
        self.test_content.update_content(new_content, new_markdown)

        # Check if content and markdown are updated
        self.assertEqual(self.test_content.content, new_content)
        self.assertEqual(self.test_content.markdown, new_markdown)

        # Check if last_updated is updated
        self.assertGreater(self.test_content.last_updated,
                           original_last_updated)

    def test_add_tags(self):
        """Test adding tags."""
        # Add tags
        self.test_content.add_tags(["tag1", "tag2"])
        self.assertEqual(self.test_content.tags, ["tag1", "tag2"])

        # Add more tags
        self.test_content.add_tags(["tag2", "tag3"])
        self.assertEqual(self.test_content.tags, ["tag1", "tag2", "tag3"])

        # Check for duplicates
        self.test_content.add_tags(["tag1", "tag3"])
        self.assertEqual(self.test_content.tags, ["tag1", "tag2", "tag3"])

    def test_update_embeddings(self):
        """Test updating embeddings."""
        embeddings = [0.1, 0.2, 0.3]
        self.test_content.update_embeddings(embeddings)
        self.assertEqual(self.test_content.embeddings, embeddings)

    def test_update_quality_metrics(self):
        """Test updating quality metrics."""
        metrics = {"completeness": 0.8, "readability": 0.7}
        self.test_content.update_quality_metrics(metrics)
        self.assertEqual(self.test_content.quality_metrics, metrics)

    def test_update_summary(self):
        """Test updating summary."""
        summary = "This is a summary of the test content."
        summary_type = "concise"

        # Store the original last_updated
        original_last_updated = self.test_content.last_updated

        # Update summary
        self.test_content.update_summary(summary, summary_type)

        # Check if summary and summary_type are updated
        self.assertEqual(self.test_content.summary, summary)
        self.assertEqual(self.test_content.summary_type, summary_type)

        # Check if last_updated is updated
        self.assertGreater(self.test_content.last_updated,
                           original_last_updated)

    def test_to_dict(self):
        """Test converting WebContent to dictionary."""
        # Add some data to test
        self.test_content.embeddings = [0.1, 0.2, 0.3]
        self.test_content.tags = ["tag1", "tag2"]
        self.test_content.quality_metrics = {
            "completeness": 0.8, "readability": 0.7}
        self.test_content.summary = "This is a summary."
        self.test_content.summary_type = "concise"

        # Convert to dictionary
        content_dict = self.test_content.to_dict()

        # Check if all fields are included
        self.assertEqual(content_dict["id"], "test-id")
        self.assertEqual(content_dict["url"], "https://example.com")
        self.assertEqual(content_dict["title"], "Test Title")
        self.assertEqual(content_dict["content"], "This is a test content.")
        self.assertEqual(content_dict["markdown"],
                         "# Test Title\n\nThis is a test content.")
        self.assertEqual(content_dict["metadata"], {
                         "author": "Test Author", "published_date": "2023-01-01"})
        self.assertEqual(content_dict["embeddings"], [0.1, 0.2, 0.3])
        self.assertEqual(content_dict["tags"], ["tag1", "tag2"])
        self.assertIsInstance(content_dict["timestamp"], str)
        self.assertIsInstance(content_dict["last_updated"], str)
        self.assertEqual(content_dict["relevance_score"], 0.0)
        self.assertEqual(content_dict["quality_metrics"], {
                         "completeness": 0.8, "readability": 0.7})
        self.assertEqual(content_dict["summary"], "This is a summary.")
        self.assertEqual(content_dict["summary_type"], "concise")

    def test_from_dict(self):
        """Test creating WebContent from dictionary."""
        # Create a dictionary
        content_dict = {
            "id": "test-id",
            "url": "https://example.com",
            "title": "Test Title",
            "content": "This is a test content.",
            "markdown": "# Test Title\n\nThis is a test content.",
            "metadata": {"author": "Test Author", "published_date": "2023-01-01"},
            "embeddings": [0.1, 0.2, 0.3],
            "tags": ["tag1", "tag2"],
            "timestamp": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "relevance_score": 0.5,
            "quality_metrics": {"completeness": 0.8, "readability": 0.7},
            "summary": "This is a summary.",
            "summary_type": "concise"
        }

        # Create WebContent from dictionary
        content = WebContent.from_dict(content_dict)

        # Check if all fields are correctly set
        self.assertEqual(content.id, "test-id")
        self.assertEqual(content.url, "https://example.com")
        self.assertEqual(content.title, "Test Title")
        self.assertEqual(content.content, "This is a test content.")
        self.assertEqual(content.markdown,
                         "# Test Title\n\nThis is a test content.")
        self.assertEqual(content.metadata, {
                         "author": "Test Author", "published_date": "2023-01-01"})
        self.assertEqual(content.embeddings, [0.1, 0.2, 0.3])
        self.assertEqual(content.tags, ["tag1", "tag2"])
        self.assertIsInstance(content.timestamp, datetime)
        self.assertIsInstance(content.last_updated, datetime)
        self.assertEqual(content.relevance_score, 0.5)
        self.assertEqual(content.quality_metrics, {
                         "completeness": 0.8, "readability": 0.7})
        self.assertEqual(content.summary, "This is a summary.")
        self.assertEqual(content.summary_type, "concise")


if __name__ == "__main__":
    unittest.main()
