from typing import Dict, Any, Optional, List, Union
import tiktoken
from .web_content import WebContent


class ContentSummarizer:
    """Summarizes web content using LLM."""

    def __init__(self, llm_client):
        """Initialize the content summarizer.

        Args:
            llm_client: LLM client for generating summaries
        """
        if not llm_client:
            raise ValueError("LLM client is required for ContentSummarizer")
        self.llm_client = llm_client
        self.max_chunk_size = 1000  # Maximum size of content chunks

    def summarize_content(self, content: Union[str, WebContent], summary_type: str = "concise") -> str:
        """Summarize content using LLM.

        Args:
            content: Content to summarize (string or WebContent object)
            summary_type: Type of summary to generate (concise, detailed, key_points)

        Returns:
            Generated summary
        """
        # Get text to summarize
        text_to_summarize = content.content if isinstance(
            content, WebContent) else content

        # Validate summary type
        if summary_type not in ["concise", "detailed", "key_points"]:
            raise ValueError(f"Invalid summary type: {summary_type}")

        # Get summary prompt
        prompt = self._get_summary_prompt(summary_type)

        # Generate summary
        summary = self.llm_client.generate_summary(text_to_summarize, prompt)

        return summary

    def _chunk_content(self, content: str) -> List[str]:
        """Split content into chunks for processing.

        Args:
            content: Content to split

        Returns:
            List of content chunks
        """
        # Split content into sentences
        sentences = content.split('. ')

        chunks = []
        current_chunk = []
        current_size = 0

        for sentence in sentences:
            sentence_size = len(sentence)

            # If adding this sentence would exceed max chunk size, start a new chunk
            if current_size + sentence_size > self.max_chunk_size:
                if current_chunk:
                    chunks.append('. '.join(current_chunk) + '.')
                current_chunk = [sentence]
                current_size = sentence_size
            else:
                current_chunk.append(sentence)
                current_size += sentence_size

        # Add the last chunk if it exists
        if current_chunk:
            chunks.append('. '.join(current_chunk) + '.')

        return chunks

    def _combine_summaries(self, summaries: List[str]) -> str:
        """Combine multiple summaries into one.

        Args:
            summaries: List of summaries to combine

        Returns:
            Combined summary
        """
        if not summaries:
            raise ValueError("No summaries to combine")

        # If there's only one summary, return it
        if len(summaries) == 1:
            return summaries[0]

        # Combine summaries using LLM
        combined_text = "\n\n".join(summaries)
        prompt = "Combine the following summaries into a coherent summary:"

        combined_summary = self.llm_client.generate_summary(
            combined_text, prompt)

        return combined_summary

    def _get_summary_prompt(self, summary_type: str) -> str:
        """Get the appropriate prompt for the summary type.

        Args:
            summary_type: Type of summary to generate

        Returns:
            Summary prompt
        """
        prompts = {
            "concise": "Generate a concise summary of the following content in 2-3 sentences:",
            "detailed": "Generate a detailed summary of the following content, including key points and supporting details:",
            "key_points": "Extract the key points from the following content in a bullet-point format:"
        }

        if summary_type not in prompts:
            raise ValueError(f"Invalid summary type: {summary_type}")

        return prompts[summary_type]
