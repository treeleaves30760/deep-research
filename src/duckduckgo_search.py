from typing import TypedDict, List, Optional, Dict, Any
import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote
import re


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

    Args:
        query: Search query string
        timeout: Request timeout in seconds
        limit: Maximum number of results to return
        scrape_options: Optional scraping configuration

    Returns:
        SearchResponse containing success status, data, and any error messages
    """
    base_url = 'https://duckduckgo.com/html/'

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

        # Find all search results
        for i, result in enumerate(soup.select('.result')):
            if i >= limit:
                break

            title = result.select_one('.result__title').get_text(strip=True)
            url_element = result.select_one('.result__url')
            url = url_element.get_text(strip=True) if url_element else ''
            snippet = result.select_one(
                '.result__snippet').get_text(strip=True)

            # Get actual URL from href attribute
            link = result.select_one('.result__a')
            actual_url = ''
            if link and link.get('href'):
                match = re.search(r'uddg=([^&]+)', link['href'])
                if match:
                    actual_url = unquote(match.group(1))

            document: FirecrawlDocument = {
                'url': actual_url or url,
                'title': title,
                'markdown': f'# {title}\n\n{snippet}',
                'actions': None
            }

            results.append(document)

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
    response = search('python programming', limit=3)
    if response['success']:
        for doc in response['data']:
            print(f"\nTitle: {doc['title']}")
            print(f"URL: {doc['url']}")
            print(f"Snippet: {doc['markdown']}")
    else:
        print(f"Error: {response['error']}")
