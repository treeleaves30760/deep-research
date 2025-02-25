from duckduckgo_search import search
from bing_search import search_bing
from typing import Dict, Any
import requests
import json
import time
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

# Import both search modules
import sys
sys.path.append('.')  # Add current directory to path if needed

console = Console()


def test_search_engines(query: str = "python programming", limit: int = 3):
    """
    Test both Bing and DuckDuckGo search engines with the same query.

    Args:
        query: Search query string
        limit: Maximum number of results to return
    """
    console.print(
        Panel(f"[bold cyan]Testing Search Engines with Query:[/] {query}", expand=False))

    # Test Bing Search
    console.print("\n[bold blue]Testing Bing Search[/]")
    bing_results = test_bing_search(query, limit)

    # Add a delay between searches to avoid rate limiting
    time.sleep(2)

    # Test DuckDuckGo Search
    console.print("\n[bold orange]Testing DuckDuckGo Search[/]")
    ddg_results = test_duckduckgo_search(query, limit)

    # Compare results
    compare_results(bing_results, ddg_results)

    return bing_results, ddg_results


def test_bing_search(query: str, limit: int) -> Dict[str, Any]:
    """Test Bing search and return results."""
    try:
        console.print(f"[dim]Sending request to Bing...[/dim]")
        response = search_bing(query, limit=limit)

        # Print status
        if response['success']:
            console.print(
                f"[green]✓ Search successful! Found {len(response['data'])} results[/]")
        else:
            console.print(f"[red]✗ Search failed: {response['error']}[/]")

        # Print request details
        print_request_details("Bing", query)

        # Print results
        print_results(response)

        return response
    except Exception as e:
        console.print(f"[red bold]Error during Bing search:[/] {str(e)}")
        return {'success': False, 'data': [], 'error': str(e)}


def test_duckduckgo_search(query: str, limit: int) -> Dict[str, Any]:
    """Test DuckDuckGo search and return results."""
    try:
        console.print(f"[dim]Sending request to DuckDuckGo...[/dim]")
        response = search(query, limit=limit)

        # Print status
        if response['success']:
            console.print(
                f"[green]✓ Search successful! Found {len(response['data'])} results[/]")
        else:
            console.print(f"[red]✗ Search failed: {response['error']}[/]")

        # Print request details
        print_request_details("DuckDuckGo", query)

        # Print results
        print_results(response)

        return response
    except Exception as e:
        console.print(f"[red bold]Error during DuckDuckGo search:[/] {str(e)}")
        return {'success': False, 'data': [], 'error': str(e)}


def print_request_details(engine: str, query: str):
    """Print details about the request for debugging."""
    console.print(f"[bold]Request Details:[/]")
    console.print(f"  Search Engine: {engine}")
    console.print(f"  Query: {query}")


def print_results(response: Dict[str, Any]):
    """Print search results in a readable format."""
    if not response['success']:
        console.print(f"[red]Error: {response['error']}[/]")
        return

    if not response['data']:
        console.print("[yellow]No results found[/]")
        return

    console.print("[bold]Search Results:[/]")

    table = Table(show_header=True, header_style="bold")
    table.add_column("Title")
    table.add_column("URL")

    for i, result in enumerate(response['data'], 1):
        table.add_row(
            result['title'],
            result['url']
        )

    console.print(table)

    # Print first result in detail
    if response['data']:
        console.print("\n[bold]First Result Details:[/]")
        first_result = response['data'][0]
        console.print(f"Title: {first_result['title']}")
        console.print(f"URL: {first_result['url']}")
        console.print("Content:")
        console.print(Panel(first_result['markdown'], expand=False))


def compare_results(bing_response: Dict[str, Any], ddg_response: Dict[str, Any]):
    """Compare results from both search engines."""
    console.print("\n[bold purple]Comparison Summary[/]")

    bing_success = bing_response.get('success', False)
    ddg_success = ddg_response.get('success', False)

    bing_count = len(bing_response.get('data', [])) if bing_success else 0
    ddg_count = len(ddg_response.get('data', [])) if ddg_success else 0

    table = Table(show_header=True, header_style="bold")
    table.add_column("Engine")
    table.add_column("Status")
    table.add_column("Results Count")
    table.add_column("Error (if any)")

    table.add_row(
        "Bing",
        "[green]Success[/]" if bing_success else "[red]Failed[/]",
        str(bing_count),
        bing_response.get('error', 'None') if not bing_success else 'None'
    )

    table.add_row(
        "DuckDuckGo",
        "[green]Success[/]" if ddg_success else "[red]Failed[/]",
        str(ddg_count),
        ddg_response.get('error', 'None') if not ddg_success else 'None'
    )

    console.print(table)


def verbose_duckduckgo_request(query: str):
    """Make a direct request to DuckDuckGo with verbose output to debug issues."""
    console.print(
        Panel("[bold orange]Verbose DuckDuckGo Request Debug[/]", expand=False))

    base_url = 'https://duckduckgo.com/html/'

    # Browser-like headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://duckduckgo.com/',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-site',
        'DNT': '1',
        'Cache-Control': 'max-age=0',
    }

    try:
        console.print(
            "[bold]Step 1:[/] Creating session and visiting homepage")
        session = requests.Session()
        homepage_response = session.get(
            'https://duckduckgo.com/', headers=headers)

        console.print(f"Homepage status code: {homepage_response.status_code}")
        console.print(f"Cookies received: {session.cookies.get_dict()}")

        console.print("\n[bold]Step 2:[/] Making search request")
        response = session.get(
            base_url,
            params={'q': query},
            headers=headers
        )

        console.print(f"Search status code: {response.status_code}")
        console.print(f"Response headers: {dict(response.headers)}")

        # Check if we got HTML
        if 'text/html' in response.headers.get('Content-Type', ''):
            console.print("[green]Received HTML response[/]")

            # Save the HTML response to a file for inspection
            with open('ddg_response.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            console.print(
                "[green]Saved HTML response to 'ddg_response.html'[/]")

            # Check for signs of blocking
            if 'robot' in response.text.lower() or 'captcha' in response.text.lower():
                console.print(
                    "[red]Possible bot detection! Found robot/captcha references in the response.[/]")

            # Print first 500 chars of the response
            console.print("\n[bold]Response preview:[/]")
            console.print(
                response.text[:500] + "..." if len(response.text) > 500 else response.text)
        else:
            console.print(
                f"[yellow]Unexpected content type: {response.headers.get('Content-Type', 'unknown')}[/]")

        return response
    except Exception as e:
        console.print(f"[red bold]Error during verbose request:[/] {str(e)}")
        return None


if __name__ == "__main__":
    console.print("[bold]Search Engine Diagnostic Tool[/]\n")

    # Ask for a search query
    query = input("Enter search query (default: 'python programming'): ").strip(
    ) or "python programming"

    # Run tests
    bing_results, ddg_results = test_search_engines(query)

    # If DuckDuckGo failed, run verbose debug
    if not ddg_results.get('success', False):
        console.print(
            "\n[bold red]DuckDuckGo search failed, running verbose debug...[/]")
        verbose_duckduckgo_request(query)
