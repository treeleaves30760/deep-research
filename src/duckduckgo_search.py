from typing import TypedDict, List, Optional, Dict, Any
import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote
import re
import time
import random


class FirecrawlDocument(TypedDict):
    url: str
    title: str
    markdown: str
    actions: None


class SearchResponse(TypedDict):
    success: bool
    data: List[FirecrawlDocument]
    error: Optional[str]


def search(
    query: str,
    timeout: int = 15,
    limit: int = 5,
    scrape_options: Optional[Dict[str, List[str]]] = None
) -> SearchResponse:
    """
    Search DuckDuckGo and return results in a structured format.

    Supports special tag format: <search_words>specific search phrase</search_words>

    Args:
        query: Search query string
        timeout: Request timeout in seconds
        limit: Maximum number of results to return
        scrape_options: Optional scraping configuration

    Returns:
        SearchResponse containing success status, data, and any error messages
    """
    base_url = 'https://duckduckgo.com/html/'

    # Process special search word tags if present
    search_words_pattern = r'<search_words>(.*?)</search_words>'
    search_words_match = re.search(search_words_pattern, query)

    if search_words_match:
        # Extract content within search_words tags
        search_words = search_words_match.group(1).strip()

        # Replace the entire tag with the extracted content for the actual search
        query = re.sub(search_words_pattern, search_words, query)

        # Add quotes around the search words to ensure they're searched as a phrase
        query = query.replace(search_words, f'"{search_words}"')

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    }

    try:
        response = requests.get(
            base_url,
            params={'q': query},
            headers=headers,
            timeout=timeout
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        results: List[FirecrawlDocument] = []

        # Find all organic search results (exclude ads)
        # First look for the React-based results
        organic_results = soup.select('article[data-layout="organic"]')

        # If we can't find React layout results, try the old HTML structure
        if not organic_results:
            organic_results = [result for result in soup.select('.result')
                               if not result.select_one('.badge--ad') and not result.get('data-nrn') == 'ad']

        count = 0
        for result in organic_results:
            if count >= limit:
                break

            # Different extraction methods depending on the page structure (React vs old HTML)
            if result.select_one('h2 a[data-testid="result-title-a"]'):
                # New React-based layout
                title_elem = result.select_one(
                    'h2 a[data-testid="result-title-a"]')
                title = title_elem.get_text(
                    strip=True) if title_elem else "No title"

                url_element = result.select_one(
                    'a[data-testid="result-extras-url-link"]')
                snippet_elem = result.select_one('div[data-result="snippet"]')

            else:
                # Old HTML layout
                title_elem = result.select_one('.result__title a')
                title = title_elem.get_text(
                    strip=True) if title_elem else "No title"

                url_element = result.select_one('.result__url')
                snippet_elem = result.select_one('.result__snippet')

            # Extract URL
            url = url_element.get_text(strip=True) if url_element else ''
            # Get actual URL
            actual_url = ''
            link = title_elem if title_elem else None
            if link and link.get('href'):
                if link['href'].startswith('http'):
                    actual_url = link['href']
                else:
                    match = re.search(r'uddg=([^&]+)', link['href'])
                    if match:
                        actual_url = unquote(match.group(1))

            # Extract snippet
            snippet = snippet_elem.get_text(
                strip=True) if snippet_elem else 'No description available'

            document: FirecrawlDocument = {
                'url': actual_url or url,
                'title': title,
                'markdown': f'# {title}\n\n{snippet}',
                'actions': None
            }

            results.append(document)
            count += 1

        return {
            'success': True,
            'data': results,
            'error': None
        }

    except requests.Timeout:
        return {
            'success': False,
            'data': [],
            'error': 'Timeout'
        }
    except Exception as e:
        return {
            'success': False,
            'data': [],
            'error': str(e)
        }


# Example usage
if __name__ == '__main__':
    # Test regular search
    response = search('python programming', limit=3)
    if response['success']:
        print("Regular search results:")
        for doc in response['data']:
            print(f"\nTitle: {doc['title']}")
            print(f"URL: {doc['url']}")
            print(f"Snippet: {doc['markdown']}")
    else:
        print(f"Error: {response['error']}")

    # Test with search_words tags
    response = search(
        'tutorials for <search_words>python machine learning</search_words> beginners', limit=3)
    if response['success']:
        print("\nSearch with tags results:")
        for doc in response['data']:
            print(f"\nTitle: {doc['title']}")
            print(f"URL: {doc['url']}")
            print(f"Snippet: {doc['markdown']}")
    else:
        print(f"Error: {response['error']}")
