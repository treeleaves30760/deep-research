from typing import Dict, Any, Union
import re
from datetime import datetime
from .web_content import WebContent


class ContentQualityChecker:
    """Class for checking and assessing the quality of web content."""

    def __init__(self):
        """Initialize the ContentQualityChecker."""
        # Minimum thresholds for quality metrics
        self.min_content_length = 100  # Minimum characters
        self.min_word_count = 20  # Minimum words
        self.max_duplicate_ratio = 0.3  # Maximum ratio of duplicate content
        self.min_readability_score = 0.5  # Minimum readability score (0-1)

    def check_quality(self, content: Union[WebContent, str]) -> Dict[str, float]:
        """
        Check the quality of web content and return quality metrics.

        Args:
            content: WebContent object or string to check

        Returns:
            Dictionary containing quality metrics
        """
        # Extract text content based on input type
        if isinstance(content, WebContent):
            text_content = content.content
        else:
            text_content = content

        metrics = {
            'completeness': self._check_completeness(text_content),
            'readability': self._check_readability(text_content),
            'coherence': self._check_coherence(text_content),
            'relevance': self._check_relevance(text_content)
        }

        # Add additional metrics for WebContent objects
        if isinstance(content, WebContent):
            metrics['freshness'] = self._check_freshness(content)
            metrics['reliability'] = self._check_reliability(content)
            metrics['uniqueness'] = self._check_uniqueness(content)

            # Calculate overall quality score
            metrics['overall_quality'] = sum(metrics.values()) / len(metrics)

        return metrics

    # Alias for backward compatibility
    check_content_quality = check_quality

    def _check_completeness(self, content: str) -> float:
        """
        Check if the content is complete and well-structured.

        Returns:
            Float between 0 and 1 indicating completeness score
        """
        score = 1.0

        # Check content length
        if len(content) < self.min_content_length:
            score *= 0.5

        # Check word count
        word_count = len(content.split())
        if word_count < self.min_word_count:
            score *= 0.5

        # Check for basic structure
        has_title = bool(re.search(r'^#\s+.+', content, re.MULTILINE))
        has_paragraphs = len(re.findall(r'\n\n', content)) > 1
        has_conclusion = bool(
            re.search(r'(conclusion|summary|in conclusion)', content.lower()))

        # Calculate score based on structure
        structure_score = 0.0
        if has_title:
            structure_score += 0.2
        if has_paragraphs:
            structure_score += 0.4
        if has_conclusion:
            structure_score += 0.4

        # Combine scores
        return min(score * (0.7 + 0.3 * structure_score), 1.0)

    def _check_readability(self, content: str) -> float:
        """
        Check the readability of the content.

        Returns:
            Float between 0 and 1 indicating readability score
        """
        # Split into sentences
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return 0.0

        # Calculate average sentence length
        avg_sentence_length = sum(len(s.split())
                                  for s in sentences) / len(sentences)

        # Calculate score based on sentence length
        if avg_sentence_length <= 10:
            sentence_score = 1.0
        elif avg_sentence_length <= 15:
            sentence_score = 0.8
        elif avg_sentence_length <= 20:
            sentence_score = 0.6
        elif avg_sentence_length <= 25:
            sentence_score = 0.4
        else:
            sentence_score = 0.2

        # Calculate average word length
        words = content.split()
        if not words:
            return 0.0

        avg_word_length = sum(len(word) for word in words) / len(words)

        # Score based on word length
        if avg_word_length <= 4:
            word_score = 1.0
        elif avg_word_length <= 5:
            word_score = 0.8
        elif avg_word_length <= 6:
            word_score = 0.6
        elif avg_word_length <= 7:
            word_score = 0.4
        else:
            word_score = 0.2

        # Combine scores
        return (sentence_score + word_score) / 2

    def _check_coherence(self, content: str) -> float:
        """
        Check the coherence of the content.

        Returns:
            Float between 0 and 1 indicating coherence score
        """
        # Split into paragraphs
        paragraphs = re.split(r'\n\n', content)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        if len(paragraphs) < 2:
            return 0.5

        # Check for transition words between paragraphs
        transition_words = [
            'however', 'therefore', 'furthermore', 'moreover',
            'consequently', 'additionally', 'also', 'next',
            'then', 'finally', 'in addition', 'besides'
        ]

        # Count paragraphs with transition words
        transitions = 0
        for i in range(1, len(paragraphs)):
            first_words = ' '.join(paragraphs[i].split()[:5]).lower()
            if any(word in first_words for word in transition_words):
                transitions += 1

        # Calculate score based on transitions
        score = transitions / (len(paragraphs) - 1)

        return min(score, 1.0)

    def _check_relevance(self, content: str, query: str = None) -> float:
        """
        Check the relevance of the content.

        Args:
            content: Content to check
            query: Optional query to check relevance against

        Returns:
            Float between 0 and 1 indicating relevance score
        """
        # If no query is provided, return a default score
        if not query:
            return 0.7

        # Simple keyword matching for relevance
        content_lower = content.lower()
        query_lower = query.lower()

        # Count occurrences of query terms
        query_terms = query_lower.split()
        matches = sum(content_lower.count(term) for term in query_terms)

        # Calculate relevance score
        if matches == 0:
            return 0.3
        elif matches < 3:
            return 0.5
        elif matches < 5:
            return 0.7
        else:
            return 0.9

    def _check_freshness(self, content: WebContent) -> float:
        """
        Check how fresh/recent the content is.

        Returns:
            Float between 0 and 1 indicating freshness score
        """
        if not content.timestamp:
            return 0.5  # Default score if no timestamp

        age_days = (datetime.now() - content.timestamp).days

        # Score decreases as content gets older
        if age_days <= 7:  # Less than a week old
            return 1.0
        elif age_days <= 30:  # Less than a month old
            return 0.8
        elif age_days <= 90:  # Less than 3 months old
            return 0.6
        elif age_days <= 365:  # Less than a year old
            return 0.4
        else:
            return 0.2

    def _check_reliability(self, content: WebContent) -> float:
        """
        Check the reliability of the content based on metadata and source.

        Returns:
            Float between 0 and 1 indicating reliability score
        """
        score = 0.5  # Base score

        # Check if URL is from a reliable domain
        reliable_domains = ['.edu', '.gov',
                            '.org', 'wikipedia.org', 'github.com']
        if any(domain in content.url.lower() for domain in reliable_domains):
            score += 0.2

        # Check if metadata contains author information
        if content.metadata.get('author'):
            score += 0.15

        # Check if metadata contains publication date
        if content.metadata.get('published_date'):
            score += 0.15

        return min(1.0, score)

    def _check_uniqueness(self, content: WebContent) -> float:
        """
        Check how unique the content is (avoid duplicate content).

        Returns:
            Float between 0 and 1 indicating uniqueness score
        """
        text = content.content.lower()
        words = text.split()

        if not words:
            return 0.0

        # Check for repeated phrases (3 or more words)
        repeated_phrases = 0
        for i in range(len(words) - 2):
            phrase = ' '.join(words[i:i+3])
            if text.count(phrase) > 1:
                repeated_phrases += 1

        # Calculate ratio of repeated phrases
        phrase_ratio = repeated_phrases / \
            (len(words) - 2) if len(words) > 2 else 0

        # Score decreases as more duplicate content is found
        return max(0.0, 1.0 - (phrase_ratio / self.max_duplicate_ratio))
