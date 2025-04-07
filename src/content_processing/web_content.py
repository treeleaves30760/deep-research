from datetime import datetime
from typing import Dict, List, Optional, Any


class WebContent:
    """Represents processed web content."""

    def __init__(
        self,
        url: str,
        content: str,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        timestamp: Optional[datetime] = None,
        summary: Optional[str] = None,
        summary_type: Optional[str] = None
    ):
        """
        Initialize a WebContent object.

        Args:
            url: URL of the web content
            content: Raw content of the web page
            title: Optional title of the content
            metadata: Optional dictionary of metadata
            tags: Optional list of tags
            timestamp: Optional timestamp of when the content was created/fetched
            summary: Optional summary of the content
            summary_type: Optional type of summary (e.g., 'concise', 'detailed')
        """
        self.url = url
        self.content = content
        self.title = title
        self.metadata = metadata or {}
        self.tags = tags or []
        self.timestamp = timestamp or datetime.now()
        self.summary = summary
        self.summary_type = summary_type
        self.last_updated = datetime.now()
        self.id = None
        self.markdown = None
        self.embeddings = None
        self.relevance_score = 0.0
        self.quality_metrics = {}

    def update_content(self, new_content: str) -> None:
        """
        Update the content of the WebContent object.

        Args:
            new_content: New content to set
        """
        self.content = new_content
        self.last_updated = datetime.now()

    def add_tag(self, tag: str) -> None:
        """
        Add a tag to the content.

        Args:
            tag: Tag to add
        """
        if tag not in self.tags:
            self.tags.append(tag)
            self.last_updated = datetime.now()

    def remove_tag(self, tag: str) -> None:
        """
        Remove a tag from the content.

        Args:
            tag: Tag to remove
        """
        if tag in self.tags:
            self.tags.remove(tag)
            self.last_updated = datetime.now()

    def update_metadata(self, key: str, value: Any) -> None:
        """
        Update a metadata field.

        Args:
            key: Metadata key
            value: New value
        """
        self.metadata[key] = value
        self.last_updated = datetime.now()

    def update_summary(self, summary: str, summary_type: str) -> None:
        """
        Update the summary of the content.

        Args:
            summary: New summary text
            summary_type: Type of summary (e.g., 'concise', 'detailed')
        """
        self.summary = summary
        self.summary_type = summary_type
        self.last_updated = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the WebContent object to a dictionary.

        Returns:
            Dictionary representation of the WebContent object
        """
        return {
            'url': self.url,
            'content': self.content,
            'title': self.title,
            'metadata': self.metadata,
            'tags': self.tags,
            'timestamp': self.timestamp.isoformat(),
            'last_updated': self.last_updated.isoformat(),
            'summary': self.summary,
            'summary_type': self.summary_type,
            'quality_metrics': self.quality_metrics
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WebContent':
        """
        Create a WebContent object from a dictionary.

        Args:
            data: Dictionary containing WebContent data

        Returns:
            WebContent object
        """
        content = cls(
            url=data['url'],
            content=data['content'],
            title=data.get('title'),
            metadata=data.get('metadata'),
            tags=data.get('tags'),
            timestamp=datetime.fromisoformat(
                data['timestamp']) if data.get('timestamp') else None,
            summary=data.get('summary'),
            summary_type=data.get('summary_type')
        )

        # Set quality metrics if available
        if 'quality_metrics' in data:
            content.quality_metrics = data['quality_metrics']

        return content

    def update_embeddings(self, embeddings: List[float]) -> None:
        """Update content embeddings.

        Args:
            embeddings: New embeddings
        """
        self.embeddings = embeddings
        self.last_updated = datetime.now()

    def update_quality_metrics(self, metrics: Dict[str, float]) -> None:
        """Update content quality metrics.

        Args:
            metrics: New quality metrics
        """
        self.quality_metrics = metrics
        self.last_updated = datetime.now()
