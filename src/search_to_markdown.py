import os
import time
import random
from typing import List, Dict, Any, Optional

# Import your existing modules
from content_extract.website_to_markdown import WebsiteToMarkdown
from search_engine.duckduckgo_search import search as duckduckgo_search
from search_engine.bing_search import search_bing
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path


class SearchToMarkdown:
    """
    A class that combines search functionality with WebsiteToMarkdown conversion.
    """

    def __init__(self, output_dir="search_results", render_js=True, wait_time=5, headless=True):
        """
        Initialize the SearchToMarkdown converter.

        Args:
            output_dir (str): Directory to save markdown files
            render_js (bool): Whether to render JavaScript when converting to markdown
            wait_time (int): Wait time in seconds for page loading
            headless (bool): Whether to run browser in headless mode
        """
        self.output_dir = output_dir
        self.render_js = render_js
        self.wait_time = wait_time
        self.markdown_converter = WebsiteToMarkdown(
            headless=headless, wait_time=wait_time)
        self.console = Console()

        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def search_and_convert(self,
                           query: str,
                           engine: str = "duckduckgo",
                           limit: int = 5,
                           convert_results: bool = True,
                           use_readability: bool = True) -> Dict[str, Any]:
        """
        Search using the specified engine and convert results to markdown.

        Args:
            query (str): Search query
            engine (str): Search engine to use ("duckduckgo" or "bing")
            limit (int): Maximum number of results to return
            convert_results (bool): Whether to convert results to markdown
            use_readability (bool): Whether to use readability for content extraction

        Returns:
            Dict: Results and their markdown conversions
        """
        self.console.print(
            Panel(f"[bold cyan]Searching with {engine} for:[/] {query}", expand=False))

        # Perform the search
        with Progress(
            SpinnerColumn(),
            TextColumn(f"[bold yellow]Searching {engine}...[/]"),
            transient=True,
        ) as progress:
            progress.add_task("searching", total=None)

            if engine.lower() == "duckduckgo":
                results = duckduckgo_search(query, limit=limit)
            elif engine.lower() == "bing":
                results = search_bing(query, limit=limit)
            else:
                return {"success": False, "error": "Unsupported search engine"}

        # Handle search failure
        if not results['success']:
            self.console.print(f"[red]Search failed: {results['error']}[/]")
            return results

        # Display search results
        self.console.print(f"[green]Found {len(results['data'])} results[/]")
        for i, result in enumerate(results['data']):
            self.console.print(f"  [bold]{i+1}.[/] {result['title']}")
            self.console.print(f"  [dim]{result['url']}[/dim]")
            self.console.print("")

        # Convert results to markdown if requested
        if convert_results and results['success']:
            # Create a folder for this search query
            search_folder = self._create_search_folder(query)

            results['markdown_files'] = []

            for i, result in enumerate(results['data']):
                url = result['url']
                title = result['title']

                self.console.print(
                    f"[bold cyan]Converting result {i+1}/{len(results['data'])}:[/] {title}")

                try:
                    # Create a filename based on the result title
                    safe_title = "".join(
                        c if c.isalnum() else "_" for c in title)
                    filename = f"{i+1}_{safe_title[:50]}.md"
                    output_file = os.path.join(search_folder, filename)

                    with Progress(
                        SpinnerColumn(),
                        TextColumn(f"[bold blue]Converting to markdown...[/]"),
                        transient=True,
                    ) as progress:
                        progress.add_task("converting", total=None)

                        # Convert the URL to markdown and save it
                        success = self.markdown_converter.save_as_markdown(
                            url,
                            output_file,
                            render_js=self.render_js,
                            wait_time=self.wait_time,
                            use_readability=use_readability
                        )

                    if success:
                        self.console.print(
                            f"  [green]Successfully saved to {output_file}[/]")
                        results['data'][i]['markdown_file'] = output_file
                        results['markdown_files'].append(output_file)
                    else:
                        self.console.print(
                            f"  [yellow]Failed to convert {url}[/]")

                    # Add a random delay between conversions to avoid rate limiting
                    # Don't sleep after the last conversion
                    if i < len(results['data']) - 1:
                        sleep_time = random.uniform(1, 3)
                        with Progress(
                            SpinnerColumn(),
                            TextColumn(
                                f"[bold blue]Waiting {sleep_time:.1f} seconds before next conversion...[/]"),
                            transient=True,
                        ) as progress:
                            progress.add_task("sleeping", total=None)
                            time.sleep(sleep_time)

                except Exception as e:
                    self.console.print(
                        f"  [red]Error converting {url}: {str(e)}[/]")

            self.console.print(
                f"[green]All conversions completed. Files saved to: {search_folder}[/]")

        return results

    def _create_search_folder(self, query: str) -> str:
        """
        Create a folder for this search query.

        Args:
            query (str): Search query

        Returns:
            str: Path to the created folder
        """
        # Create a safe folder name from the query
        safe_query = "".join(c if c.isalnum() else "_" for c in query)
        safe_query = safe_query[:30]  # Limit length

        # Add timestamp to make folder unique
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        folder_name = f"{safe_query}_{timestamp}"

        # Create the full path
        folder_path = os.path.join(self.output_dir, folder_name)

        # Create the folder
        os.makedirs(folder_path, exist_ok=True)

        return folder_path

    def read_markdown_file(self, file_path: str) -> str:
        """
        Read a markdown file.

        Args:
            file_path (str): Path to the markdown file

        Returns:
            str: Content of the markdown file
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.console.print(
                f"[red]Error reading file {file_path}: {str(e)}[/]")
            return ""

    def close(self):
        """
        Close the WebsiteToMarkdown converter.
        """
        if self.markdown_converter:
            self.markdown_converter.close()

    def __del__(self):
        """
        Ensure resources are cleaned up.
        """
        self.close()


def search_to_markdown(query: str,
                       engine: str = "duckduckgo",
                       limit: int = 5,
                       output_dir: str = "search_results",
                       render_js: bool = True,
                       wait_time: int = 5,
                       use_readability: bool = True) -> Dict[str, Any]:
    """
    Convenience function to search and convert results to markdown.

    Args:
        query (str): Search query
        engine (str): Search engine to use ("duckduckgo" or "bing")
        limit (int): Maximum number of results to return
        output_dir (str): Directory to save markdown files
        render_js (bool): Whether to render JavaScript when converting to markdown
        wait_time (int): Wait time in seconds for page loading
        use_readability (bool): Whether to use readability for content extraction

    Returns:
        Dict: Results and their markdown conversions
    """
    converter = SearchToMarkdown(
        output_dir=output_dir,
        render_js=render_js,
        wait_time=wait_time
    )

    try:
        results = converter.search_and_convert(
            query=query,
            engine=engine,
            limit=limit,
            convert_results=True,
            use_readability=use_readability
        )
        return results
    finally:
        converter.close()


if __name__ == "__main__":
    # Example usage
    query = input("Enter search query: ")
    engine = input(
        "Enter search engine (duckduckgo or bing): ").lower() or "duckduckgo"
    limit = int(input("Enter number of results (default 3): ") or "3")

    results = search_to_markdown(
        query=query,
        engine=engine,
        limit=limit,
        render_js=True,
        wait_time=5
    )

    if results['success'] and 'markdown_files' in results:
        print(f"\nSearch and conversion successful!")
        print(f"Markdown files saved to: {results['markdown_files']}")
    else:
        print(
            f"\nSearch or conversion failed: {results.get('error', 'Unknown error')}")
