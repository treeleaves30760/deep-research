import unittest
from datetime import datetime
from src.content_processing.web_content import WebContent


class TestWebContent(unittest.TestCase):
    """Test cases for the WebContent class."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_content = WebContent(
            url="https://example.com",
            content="Test content",
            title="Test Title",
            metadata={"author": "Test Author"},
            tags=["test", "example"],
            timestamp=datetime.now()
        )

    def test_initialization(self):
        """Test the initialization of WebContent."""
        self.assertEqual(self.test_content.url, "https://example.com")
        self.assertEqual(self.test_content.content, "Test content")
        self.assertEqual(self.test_content.title, "Test Title")
        self.assertEqual(self.test_content.metadata["author"], "Test Author")
        self.assertEqual(self.test_content.tags, ["test", "example"])
        self.assertIsInstance(self.test_content.timestamp, datetime)
        self.assertIsInstance(self.test_content.last_updated, datetime)

    def test_update_content(self):
        """Test updating content."""
        new_content = "Updated content"
        self.test_content.update_content(new_content)
        self.assertEqual(self.test_content.content, new_content)
        self.assertGreater(self.test_content.last_updated,
                           self.test_content.timestamp)

    def test_add_tag(self):
        """Test adding a tag."""
        self.test_content.add_tag("new_tag")
        self.assertIn("new_tag", self.test_content.tags)
        self.assertGreater(self.test_content.last_updated,
                           self.test_content.timestamp)

    def test_remove_tag(self):
        """Test removing a tag."""
        self.test_content.remove_tag("test")
        self.assertNotIn("test", self.test_content.tags)
        self.assertGreater(self.test_content.last_updated,
                           self.test_content.timestamp)

    def test_update_metadata(self):
        """Test updating metadata."""
        self.test_content.update_metadata("source", "test")
        self.assertEqual(self.test_content.metadata["source"], "test")
        self.assertGreater(self.test_content.last_updated,
                           self.test_content.timestamp)

    def test_update_summary(self):
        """Test updating summary."""
        summary = "Test summary"
        summary_type = "concise"
        self.test_content.update_summary(summary, summary_type)
        self.assertEqual(self.test_content.summary, summary)
        self.assertEqual(self.test_content.summary_type, summary_type)
        self.assertGreater(self.test_content.last_updated,
                           self.test_content.timestamp)

    def test_to_dict(self):
        """Test converting to dictionary."""
        content_dict = self.test_content.to_dict()
        self.assertEqual(content_dict["url"], self.test_content.url)
        self.assertEqual(content_dict["content"], self.test_content.content)
        self.assertEqual(content_dict["title"], self.test_content.title)
        self.assertEqual(content_dict["metadata"], self.test_content.metadata)
        self.assertEqual(content_dict["tags"], self.test_content.tags)
        self.assertEqual(content_dict["summary"], self.test_content.summary)
        self.assertEqual(content_dict["summary_type"],
                         self.test_content.summary_type)

    def test_from_dict(self):
        """Test creating from dictionary."""
        content_dict = self.test_content.to_dict()
        new_content = WebContent.from_dict(content_dict)
        self.assertEqual(new_content.url, self.test_content.url)
        self.assertEqual(new_content.content, self.test_content.content)
        self.assertEqual(new_content.title, self.test_content.title)
        self.assertEqual(new_content.metadata, self.test_content.metadata)
        self.assertEqual(new_content.tags, self.test_content.tags)
        self.assertEqual(new_content.summary, self.test_content.summary)
        self.assertEqual(new_content.summary_type,
                         self.test_content.summary_type)


if __name__ == '__main__':
    unittest.main()
