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


def search_bing(
    query: str,
    timeout: int = 15,
    limit: int = 5,
    scrape_options: Optional[Dict[str, List[str]]] = None
) -> SearchResponse:
    """
    Search Bing and return results in a structured format.

    Args:
        query: Search query string
        timeout: Request timeout in seconds
        limit: Maximum number of results to return
        scrape_options: Optional scraping configuration

    Returns:
        SearchResponse containing success status, data, and any error messages
    """
    base_url = 'https://www.bing.com/search'

    # Extract content from search_words tags if present
    search_words_pattern = r'<search_words>(.*?)</search_words>'
    search_words_match = re.search(search_words_pattern, query)

    if search_words_match:
        # Extract content within search_words tags
        search_words = search_words_match.group(1).strip()

        # Replace the entire tag with the extracted content for the actual search
        query = re.sub(search_words_pattern, search_words, query)

        # Add quotes around the search words to ensure they're searched as a phrase
        query = query.replace(search_words, f'"{search_words}"')

    # Browser-like headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.bing.com/',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Cache-Control': 'max-age=0',
    }

    try:
        # Add a small delay to mimic human-like behavior
        time.sleep(random.uniform(0.5, 1.5))

        session = requests.Session()

        # First visit the homepage to get cookies
        session.get('https://www.bing.com/', headers=headers, timeout=timeout)

        # Now perform the search
        response = session.get(
            base_url,
            params={'q': query, 'form': 'QBLH'},
            headers=headers,
            timeout=timeout
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        results: List[FirecrawlDocument] = []

        # Find all organic search results (excluding ads)
        organic_results = soup.select('#b_results > li.b_algo')

        count = 0
        for result in organic_results:
            if count >= limit:
                break

            # Extract title and URL
            title_element = result.select_one('h2 a')
            if not title_element:
                continue

            title = title_element.get_text(strip=True)
            url = title_element.get('href', '')

            # Extract snippet
            snippet_element = result.select_one('.b_caption p')
            snippet = snippet_element.get_text(
                strip=True) if snippet_element else 'No description available'

            document: FirecrawlDocument = {
                'url': url,
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
    response = search_bing('python programming', limit=3)
    if response['success']:
        print("Regular search results:")
        for doc in response['data']:
            print(f"\nTitle: {doc['title']}")
            print(f"URL: {doc['url']}")
            print(f"Snippet: {doc['markdown']}")
    else:
        print(f"Error: {response['error']}")
