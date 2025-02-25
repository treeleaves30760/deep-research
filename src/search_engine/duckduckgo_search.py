from typing import TypedDict, List, Optional, Dict, Any
import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote
import re
import time
import random
import logging
import sys
import os
import gzip
import brotli
import zlib

# Change the following line to enable debug mode
DEBUG_MODE = False

if DEBUG_MODE:
    log_level = logging.DEBUG
else:
    log_level = logging.INFO


# Set up logging
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ddg_search_debug.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("ddg_search")


class FirecrawlDocument(TypedDict):
    url: str
    title: str
    markdown: str
    actions: None


class SearchResponse(TypedDict):
    success: bool
    data: List[FirecrawlDocument]
    error: Optional[str]
    debug_info: Optional[Dict[str, Any]]


def search(
    query: str,
    timeout: int = 15,
    limit: int = 5,
    scrape_options: Optional[Dict[str, List[str]]] = None,
    debug: bool = True
) -> SearchResponse:
    """
    Search DuckDuckGo with proper handling of compressed responses.

    Args:
        query: Search query string
        timeout: Request timeout in seconds
        limit: Maximum number of results to return
        scrape_options: Optional scraping configuration
        debug: Enable detailed debugging

    Returns:
        SearchResponse containing success status, data, error messages, and debug info
    """
    base_url = 'https://html.duckduckgo.com/html/'  # Use html subdomain directly
    debug_info = {"timestamps": {}, "response_info": {}}

    # Log start time
    debug_info["timestamps"]["start"] = time.time()
    logger.info(f"Starting search for query: {query}")

    # Browser-like headers with proper encoding support
    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        # Explicitly support gzip, deflate, and brotli
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://duckduckgo.com/',
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
        'Upgrade-Insecure-Requests': '1',
        'DNT': '1',
    }

    debug_info["headers"] = headers
    logger.debug(f"Using headers: {headers}")

    try:
        # Add a random delay before request
        delay = random.uniform(1.0, 2.0)
        logger.debug(f"Adding delay of {delay:.2f} seconds")
        time.sleep(delay)
        debug_info["timestamps"]["after_delay"] = time.time()

        # Create a session with specific config for proper content handling
        session = requests.Session()

        # Make the search request directly to html.duckduckgo.com
        logger.debug(
            f"Making search request to {base_url} with query '{query}'")

        response = session.get(
            base_url,
            params={'q': query},
            headers=headers,
            timeout=timeout
        )

        # Store response info for debugging
        debug_info["response_info"]["search"] = {
            "status_code": response.status_code,
            "url": response.url,
            "headers": dict(response.headers),
            "content_type": response.headers.get('Content-Type', 'unknown'),
            "content_encoding": response.headers.get('Content-Encoding', 'none'),
            "content_length": len(response.content),
            "apparent_encoding": response.apparent_encoding,
            "encoding": response.encoding,
        }

        logger.debug(
            f"Search request response. Status: {response.status_code}")
        logger.debug(f"Response URL: {response.url}")
        logger.debug(
            f"Content-Encoding: {response.headers.get('Content-Encoding', 'none')}")
        logger.debug(
            f"Content-Type: {response.headers.get('Content-Type', 'unknown')}")

        # Handle content based on encoding
        content = response.content
        html_text = None

        # Try to decode content based on Content-Encoding header
        content_encoding = response.headers.get('Content-Encoding', '').lower()

        if content_encoding == 'gzip' or content_encoding == 'x-gzip':
            try:
                logger.debug("Manually decompressing gzip content")
                html_text = gzip.decompress(content).decode('utf-8')
            except Exception as e:
                logger.error(f"Error decompressing gzip content: {str(e)}")
        elif content_encoding == 'br':
            try:
                logger.debug("Manually decompressing brotli content")
                html_text = brotli.decompress(content).decode('utf-8')
            except Exception as e:
                logger.error(f"Error decompressing brotli content: {str(e)}")
        elif content_encoding == 'deflate':
            try:
                logger.debug("Manually decompressing deflate content")
                html_text = zlib.decompress(content).decode('utf-8')
            except Exception as e:
                logger.error(f"Error decompressing deflate content: {str(e)}")

        # If manual decompression failed or no encoding specified, try response.text
        if not html_text:
            logger.debug("Using response.text for HTML content")
            html_text = response.text

            # If text still looks like binary/compressed data, try some fallbacks
            if not html_text or len(html_text) < 200 or '<!DOCTYPE html>' not in html_text:
                logger.debug(
                    "Response.text appears to be invalid HTML, trying fallbacks")

                # Try with different encodings
                for encoding in ['utf-8', 'latin-1', 'ISO-8859-1', 'windows-1252']:
                    try:
                        logger.debug(f"Trying to decode with {encoding}")
                        html_text = content.decode(encoding)
                        if '<!DOCTYPE html>' in html_text or '<html' in html_text:
                            logger.debug(
                                f"Successfully decoded with {encoding}")
                            break
                    except Exception:
                        pass

        # Save HTML response for debugging if requested
        if debug and html_text:
            os.makedirs("debug", exist_ok=True)
            html_filename = f"debug/ddg_response_{int(time.time())}.html"
            with open(html_filename, "w", encoding="utf-8") as f:
                f.write(html_text)
            logger.debug(f"Saved decoded HTML response to {html_filename}")
            debug_info["response_info"]["saved_html"] = html_filename

            # Also save raw content for comparison
            raw_filename = f"debug/ddg_raw_response_{int(time.time())}.bin"
            with open(raw_filename, "wb") as f:
                f.write(content)
            logger.debug(f"Saved raw response to {raw_filename}")
            debug_info["response_info"]["saved_raw"] = raw_filename

        # Check if we have valid HTML content
        if not html_text or len(html_text) < 200 or ('<!DOCTYPE html>' not in html_text and '<html' not in html_text):
            logger.error("Failed to get valid HTML content from response")
            return {
                'success': False,
                'data': [],
                'error': 'Failed to decode HTML content properly',
                'debug_info': debug_info
            }

        # Parse HTML response
        logger.debug("Parsing HTML response with BeautifulSoup")
        soup = BeautifulSoup(html_text, 'html.parser')
        results: List[FirecrawlDocument] = []

        # Check for bot detection
        if 'robot' in html_text.lower() or 'captcha' in html_text.lower():
            logger.warning("Possible bot detection in response")
            debug_info["response_info"]["possible_bot_detection"] = True

            # Still try to parse results even if bot detection is suspected

        # Find all organic search results
        debug_info["parsing"] = {"result_types": {}}

        # Try different HTML structures
        # Latest known DuckDuckGo HTML structure (Feb 2025)
        organic_results = soup.select('.result')
        debug_info["parsing"]["result_types"]["result_class"] = len(
            organic_results)
        logger.debug(
            f"Found {len(organic_results)} elements with '.result' class")

        if not organic_results:
            organic_results = soup.select('.web-result')
            debug_info["parsing"]["result_types"]["web_result_class"] = len(
                organic_results)
            logger.debug(
                f"Found {len(organic_results)} elements with '.web-result' class")

        if not organic_results:
            # This seems to be the current structure as of Feb 2025
            organic_results = soup.select('.result__body')
            debug_info["parsing"]["result_types"]["result_body_class"] = len(
                organic_results)
            logger.debug(
                f"Found {len(organic_results)} elements with '.result__body' class")

        if not organic_results:
            # Another structure sometimes used
            organic_results = soup.select('.links_main')
            debug_info["parsing"]["result_types"]["links_main_class"] = len(
                organic_results)
            logger.debug(
                f"Found {len(organic_results)} elements with '.links_main' class")

        if not organic_results:
            # Even more general selectors
            organic_results = soup.select(
                'article, .result, .web-result, .serp__results__item, #links > div')
            debug_info["parsing"]["result_types"]["general_selectors"] = len(
                organic_results)
            logger.debug(
                f"Found {len(organic_results)} elements with general selectors")

            # Filter out obvious ads
            organic_results = [result for result in organic_results
                               if not result.select_one('.badge--ad')
                               and not result.get('data-nrn') == 'ad'
                               and not 'is-ad' in (result.get('class', []) or [])]

        # Analyze page structure for debugging
        debug_info["parsing"]["page_structure"] = {
            "has_results_id": bool(soup.select('#links')),
            "has_links_class": bool(soup.select('.links')),
            "has_serp_results": bool(soup.select('.serp__results')),
            "total_articles": len(soup.select('article')),
            "total_links": len(soup.select('a')),
            "body_classes": soup.find('body').get('class', []) if soup.find('body') else [],
            "title": soup.find('title').get_text() if soup.find('title') else None,
        }

        logger.debug(
            f"Page structure analysis: {debug_info['parsing']['page_structure']}")

        # If still no results, try to find any link with text that could be a search result
        if not organic_results:
            logger.warning(
                "No structured results found, looking for any content links")
            # Try to find any links that might be results
            all_links = soup.select('a[href^="http"]')
            potential_results = []

            for link in all_links:
                # Skip links that are obviously not results
                if not link.get_text(strip=True) or len(link.get_text(strip=True)) < 5:
                    continue
                if 'duckduckgo.com' in link.get('href', ''):
                    continue
                if link.find_parent('nav'):
                    continue

                # This might be a search result
                potential_results.append(link)

            logger.debug(
                f"Found {len(potential_results)} potential result links")

            # Use these as last resort
            if potential_results and not organic_results:
                organic_results = potential_results
                debug_info["parsing"]["result_types"]["fallback_links"] = len(
                    organic_results)

        if not organic_results:
            logger.warning("No organic results found with any selector")
            # Save a snippet of HTML for debugging
            debug_info["parsing"]["html_snippet"] = html_text[:1000] if html_text else "None"
            return {
                'success': False,
                'data': [],
                'error': 'No organic results found in HTML response',
                'debug_info': debug_info
            }

        count = 0
        for result in organic_results:
            if count >= limit:
                break

            # Create debug info for this result
            result_debug = {
                "html": str(result)[:200],  # First 200 chars for debugging
                "classes": result.get('class', []) if hasattr(result, 'get') else [],
                "selectors_found": {}
            }

            # Initialize result data
            title = None
            url = None
            snippet = None

            # If result is just a link element (fallback mode)
            if result.name == 'a' and result.get('href'):
                title = result.get_text(strip=True)
                url = result.get('href')
                snippet = "No description available"
            else:
                # Standard result parsing logic
                # Try to find title and link
                title_elem = None

                # Title selectors for various DuckDuckGo layouts
                for selector in ['.result__title a', '.result__a', 'h2 a', 'h3 a', '.link', '.title a']:
                    title_elem = result.select_one(selector)
                    if title_elem:
                        result_debug["selectors_found"][f"title_{selector}"] = True
                        break

                if title_elem:
                    title = title_elem.get_text(strip=True)
                    url = title_elem.get('href')

                    # DuckDuckGo often uses redirects, extract actual URL if present
                    if url and 'uddg=' in url:
                        match = re.search(r'uddg=([^&]+)', url)
                        if match:
                            url = unquote(match.group(1))

                # If we have a result container but couldn't find title/url with selectors,
                # try a more generic approach
                if not title or not url:
                    # Look for any link with text
                    links = result.select('a[href]')
                    for link in links:
                        link_text = link.get_text(strip=True)
                        # Reasonable title length
                        if link_text and len(link_text) > 5:
                            title = link_text
                            url = link.get('href')

                            # Extract actual URL if it's a redirect
                            if url and 'uddg=' in url:
                                match = re.search(r'uddg=([^&]+)', url)
                                if match:
                                    url = unquote(match.group(1))
                            break

                # Try to find snippet
                for selector in ['.result__snippet', '.snippet', 'p', '.description']:
                    snippet_elem = result.select_one(selector)
                    if snippet_elem:
                        snippet = snippet_elem.get_text(strip=True)
                        result_debug["selectors_found"][f"snippet_{selector}"] = True
                        break

                if not snippet:
                    snippet = 'No description available'

            # Only add result if we have both title and URL
            if title and url:
                # Clean URL if needed
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url.lstrip('/')

                document: FirecrawlDocument = {
                    'url': url,
                    'title': title,
                    'markdown': f'# {title}\n\n{snippet}',
                    'actions': None
                }
                results.append(document)
                count += 1
                logger.debug(f"Added result: {title} - {url}")
            else:
                logger.debug(
                    f"Skipped result due to missing title or URL: {result_debug}")

        debug_info["timestamps"]["end"] = time.time()
        debug_info["results_count"] = len(results)

        return {
            'success': True if results else False,
            'data': results,
            'error': None if results else 'No results could be extracted',
            'debug_info': debug_info
        }

    except requests.Timeout:
        logger.error(
            f"Timeout error after {time.time() - debug_info['timestamps']['start']:.2f} seconds")
        return {
            'success': False,
            'data': [],
            'error': 'Timeout',
            'debug_info': debug_info
        }
    except Exception as e:
        logger.error(f"Error during search: {str(e)}", exc_info=True)
        return {
            'success': False,
            'data': [],
            'error': str(e),
            'debug_info': debug_info
        }


def get_random_user_agent():
    """Get a random user agent to avoid detection."""
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    ]
    return random.choice(user_agents)


if __name__ == "__main__":
    # Simple command-line interface for testing
    import sys

    query = "python programming"
    if len(sys.argv) > 1:
        query = sys.argv[1]

    print(f"Testing DuckDuckGo search with query: {query}")
    response = search(query, limit=3)

    if response['success']:
        print(f"Search successful! Found {len(response['data'])} results:")
        for i, doc in enumerate(response['data'], 1):
            print(f"\n{i}. {doc['title']}")
            print(f"   URL: {doc['url']}")
            # Safely extract snippet without backslash issues
            snippet_parts = doc['markdown'].split('\n\n')
            snippet = snippet_parts[1] if len(
                snippet_parts) > 1 else 'No snippet'
            print(f"   Snippet: {snippet}")
    else:
        print(f"Search failed: {response['error']}")
        if 'debug_info' in response:
            print("\nDebug information:")
            print(
                f"- Time elapsed: {response['debug_info']['timestamps'].get('end', time.time()) - response['debug_info']['timestamps'].get('start', 0):.2f} seconds")

            if 'parsing' in response['debug_info']:
                print("- HTML parsing info:")
                for key, value in response['debug_info']['parsing'].items():
                    if isinstance(value, dict):
                        print(f"  {key}:")
                        for k, v in value.items():
                            print(f"    {k}: {v}")
                    else:
                        print(f"  {key}: {value}")
