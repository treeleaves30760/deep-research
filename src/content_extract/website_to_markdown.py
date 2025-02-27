import os
import time
import re
import requests
import urllib.parse
import random
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from markdown import markdown
import html2text


class WebsiteToMarkdown:
    """
    A class that fetches website content and converts it to Markdown format.
    Supports JavaScript rendering for React and Vue websites.
    """

    def __init__(self, headless=True, wait_time=5):
        """
        Initialize the WebsiteToMarkdown converter.

        Args:
            headless (bool): Whether to run Chrome in headless mode
            wait_time (int): Default wait time in seconds for page to load
        """
        self.headless = headless
        self.wait_time = wait_time
        self.driver = None
        self.base_url = None

        # List of common user agents for rotation
        self.user_agents = [
            # Chrome on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
            # Firefox on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:93.0) Gecko/20100101 Firefox/93.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0",
            # Edge on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36 Edg/92.0.902.78",
            # Safari on macOS
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15",
            # Chrome on macOS
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36",
            # Firefox on macOS
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:91.0) Gecko/20100101 Firefox/91.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:92.0) Gecko/20100101 Firefox/92.0",
            # Chrome on Linux
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
            # Firefox on Linux
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:90.0) Gecko/20100101 Firefox/90.0",
            "Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0",
            # Mobile User Agents
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Android 11; Mobile; rv:68.0) Gecko/68.0 Firefox/90.0",
            "Mozilla/5.0 (Linux; Android 11; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
        ]

        # Configure HTML2Text for better markdown conversion
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.h2t.ignore_images = False
        self.h2t.ignore_tables = False
        self.h2t.body_width = 0  # No line wrapping
        self.h2t.inline_links = True
        self.h2t.wrap_links = False
        self.h2t.unicode_snob = True  # Use Unicode instead of ASCII
        self.h2t.images_to_alt = False  # Keep image links
        self.h2t.default_image_alt = "Image"  # Default alt text for images without alt
        self.h2t.skip_internal_links = False

    def _setup_driver(self):
        """Set up and return a Chrome WebDriver with randomized user agent."""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument(
                "--headless=new")  # Use new headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--log-level=3")  # Reduce logging
        chrome_options.add_argument("--silent")

        # Set a random user agent
        user_agent = random.choice(self.user_agents)
        chrome_options.add_argument(f"--user-agent={user_agent}")

        # Disable images to speed up page loading
        chrome_options.add_argument("--blink-settings=imagesEnabled=false")

        # Disable JavaScript errors and console logging
        chrome_options.add_experimental_option(
            'excludeSwitches', ['enable-logging'])

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver

    def fetch_content(self, url, render_js=True, wait_time=None):
        """
        Fetch content from a URL and return it as HTML.

        Args:
            url (str): The URL to fetch
            render_js (bool): Whether to render JavaScript
            wait_time (int): Wait time in seconds for JavaScript to render

        Returns:
            str: HTML content of the page
        """
        if wait_time is None:
            wait_time = self.wait_time

        # Store the base URL for resolving relative links later
        parsed_url = urllib.parse.urlparse(url)
        self.base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

        # Add random jitter to wait time to appear more human-like
        actual_wait_time = wait_time + random.uniform(0.5, 2.0)

        if render_js:
            # Use Selenium for JavaScript rendering
            if self.driver is None:
                self.driver = self._setup_driver()

            try:
                # Set up a proxy if available (uncomment and configure if needed)
                # proxy = "your_proxy_address:port"
                # chrome_options.add_argument(f'--proxy-server={proxy}')

                self.driver.get(url)

                # Add some random scrolling to mimic human behavior
                try:
                    # Scroll down slowly to trigger lazy loading
                    height = self.driver.execute_script(
                        "return document.body.scrollHeight")
                    for i in range(1, 5):
                        scroll_to = int(height * (i / 5))
                        self.driver.execute_script(
                            f"window.scrollTo(0, {scroll_to});")
                        # Random delay between scrolls
                        time.sleep(random.uniform(0.3, 0.7))
                except Exception as e:
                    # Ignore scroll errors
                    pass

                # Wait for the page to load completely
                time.sleep(actual_wait_time)

                # Wait for the document to be in ready state
                try:
                    WebDriverWait(self.driver, actual_wait_time).until(
                        lambda d: d.execute_script(
                            'return document.readyState') == 'complete'
                    )
                except Exception:
                    print("Page load timed out, but continuing...")

                # Try to dismiss common cookie consent dialogs and popups
                try:
                    # Common cookie consent button selectors
                    cookie_button_selectors = [
                        'button[id*="cookie"][id*="accept"]',
                        'button[class*="cookie"][class*="accept"]',
                        'a[id*="cookie"][id*="accept"]',
                        'a[class*="cookie"][class*="accept"]',
                        'button[id*="cookie-consent"]',
                        'button[id*="accept-all"]',
                        'button[id*="acceptAll"]',
                        '.accept-cookies',
                        '#accept-cookies',
                        'button:contains("Accept")',
                        'button:contains("I agree")',
                        'button:contains("Accept all")',
                        'button:contains("Allow all")'
                    ]

                    for selector in cookie_button_selectors:
                        try:
                            elements = self.driver.find_elements_by_css_selector(
                                selector)
                            if elements:
                                elements[0].click()
                                time.sleep(0.5)
                                break
                        except Exception:
                            continue
                except Exception:
                    # Ignore errors from cookie dialog handling
                    pass

                # Get the HTML after JavaScript execution
                html_content = self.driver.page_source
                return html_content
            except Exception as e:
                print(f"Error fetching content with Selenium: {e}")
                # Fall back to requests if Selenium fails
                return self._fetch_with_requests(url)
        else:
            # Use requests for non-JS websites
            return self._fetch_with_requests(url)

    def _fetch_with_requests(self, url):
        """Fetch content using the requests library with randomized user agent and retry logic."""
        max_retries = 3
        retry_delay = 2  # seconds

        for attempt in range(max_retries):
            try:
                # Select a random user agent for each attempt
                user_agent = random.choice(self.user_agents)

                headers = {
                    'User-Agent': user_agent,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',  # Do Not Track
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Cache-Control': 'max-age=0',
                }

                session = requests.Session()
                # Add a delay to mimic human browsing behavior
                time.sleep(random.uniform(0.5, 1.5))

                response = session.get(url, headers=headers, timeout=15)

                # Check if we got a successful response
                if response.status_code == 200:
                    # Set base_url based on the final URL (after any redirects)
                    parsed_url = urllib.parse.urlparse(response.url)
                    self.base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

                    return response.text
                else:
                    print(
                        f"Attempt {attempt+1}/{max_retries}: HTTP Status {response.status_code}")
                    # If we get a 403/429 (Forbidden/Too Many Requests), wait longer
                    if response.status_code in [403, 429]:
                        time.sleep(retry_delay * (attempt + 1)
                                   * 2)  # Exponential backoff
                    else:
                        time.sleep(retry_delay)

            except requests.RequestException as e:
                print(
                    f"Attempt {attempt+1}/{max_retries}: Error fetching content with requests: {e}")
                time.sleep(retry_delay * (attempt + 1))

        print(f"Failed to fetch {url} after {max_retries} attempts")
        return ""

    def _fix_relative_links(self, soup):
        """
        Convert relative URLs to absolute URLs.

        Args:
            soup (BeautifulSoup): BeautifulSoup object containing parsed HTML

        Returns:
            BeautifulSoup: BeautifulSoup object with fixed links
        """
        # Fix links
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if href.startswith('/'):
                a_tag['href'] = urllib.parse.urljoin(self.base_url, href)
            elif not href.startswith(('http://', 'https://', 'mailto:', 'tel:')):
                a_tag['href'] = urllib.parse.urljoin(self.base_url, href)

        # Fix images
        for img_tag in soup.find_all('img', src=True):
            src = img_tag['src']
            if src.startswith('/'):
                img_tag['src'] = urllib.parse.urljoin(self.base_url, src)
            elif not src.startswith(('http://', 'https://', 'data:')):
                img_tag['src'] = urllib.parse.urljoin(self.base_url, src)

        return soup

    def _clean_markdown(self, markdown_content):
        """
        Clean up markdown content to make it more readable.

        Args:
            markdown_content (str): Raw markdown content

        Returns:
            str: Cleaned markdown content
        """
        # Fix excessive newlines
        markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content)

        # Fix broken inline code blocks
        markdown_content = re.sub(r'`\s+', '`', markdown_content)
        markdown_content = re.sub(r'\s+`', '`', markdown_content)

        # Fix broken tables
        markdown_content = re.sub(r'\|\s+\|', '| |', markdown_content)

        # Fix links with excessive spaces
        markdown_content = re.sub(r'\[\s+', '[', markdown_content)
        markdown_content = re.sub(r'\s+\]', ']', markdown_content)

        # Fix broken code blocks
        markdown_content = re.sub(r'```\s+', '```\n', markdown_content)
        markdown_content = re.sub(r'\s+```', '\n```', markdown_content)

        # Remove control characters
        markdown_content = re.sub(
            r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', markdown_content)

        return markdown_content

    def html_to_markdown(self, html_content):
        """
        Convert HTML content to Markdown.

        Args:
            html_content (str): HTML content to convert

        Returns:
            str: Markdown representation of the HTML
        """
        # Parse the HTML using BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove unnecessary elements
        for element in soup.select('script, style, iframe, noscript, [role="banner"], [role="navigation"]'):
            element.extract()

        # Fix relative links
        soup = self._fix_relative_links(soup)

        # Special handling for code blocks
        for pre in soup.find_all('pre'):
            code = pre.find('code')
            if code:
                # Try to determine the language
                lang = ""
                if 'class' in code.attrs:
                    classes = code['class']
                    for cls in classes:
                        if cls.startswith(('language-', 'lang-')):
                            lang = cls.split('-')[1]
                            break

                # Add language info to the pre tag if found
                if lang:
                    pre['data-language'] = lang

        # Convert to markdown
        markdown_content = self.h2t.handle(str(soup))

        # Clean up the markdown
        markdown_content = self._clean_markdown(markdown_content)

        return markdown_content

    def _extract_title(self, soup):
        """
        Extract the title of the webpage.

        Args:
            soup (BeautifulSoup): BeautifulSoup object containing parsed HTML

        Returns:
            str: Title of the webpage
        """
        title = None

        # Try to find the main heading first
        h1 = soup.find('h1')
        if h1 and h1.text.strip():
            title = h1.text.strip()

        # If no h1, try the title tag
        if not title:
            title_tag = soup.find('title')
            if title_tag and title_tag.text.strip():
                title = title_tag.text.strip()

        # If still no title, use the URL domain
        if not title and self.base_url:
            parsed_url = urllib.parse.urlparse(self.base_url)
            title = parsed_url.netloc

        return title

    def _extract_meta_description(self, soup):
        """
        Extract the meta description of the webpage.

        Args:
            soup (BeautifulSoup): BeautifulSoup object containing parsed HTML

        Returns:
            str: Meta description of the webpage
        """
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and 'content' in meta_desc.attrs:
            return meta_desc['content'].strip()
        return None

    def url_to_markdown(self, url, render_js=True, wait_time=None, use_readability=True):
        """
        Convert a website to Markdown.

        Args:
            url (str): The URL to convert
            render_js (bool): Whether to render JavaScript
            wait_time (int): Wait time in seconds for JavaScript to render
            use_readability (bool): Whether to use readability-inspired content extraction

        Returns:
            str: Markdown representation of the website
        """
        html_content = self.fetch_content(url, render_js, wait_time)
        if not html_content:
            return "Failed to fetch content from the URL."

        # Parse HTML to extract title and description
        soup = BeautifulSoup(html_content, 'html.parser')
        title = self._extract_title(soup)
        description = self._extract_meta_description(soup)

        # Add website info header
        header = f"# {title}\n\n" if title else ""
        header += f"_{description}_\n\n" if description else ""
        header += f"**Source**: [{url}]({url})\n\n"

        # Process the HTML content
        if use_readability:
            # Use readability-inspired extraction to get the main content
            main_content_html = self.extract_content_with_readability(
                html_content)
            markdown_content = self.html_to_markdown(main_content_html)
        else:
            # Convert the entire HTML to markdown
            markdown_content = self.html_to_markdown(html_content)

        # Combine header and content
        final_markdown = header + markdown_content

        return final_markdown

    def save_as_markdown(self, url, output_file, render_js=True, wait_time=None, use_readability=True):
        """
        Save website content as a Markdown file.

        Args:
            url (str): The URL to convert
            output_file (str): Path to save the Markdown file
            render_js (bool): Whether to render JavaScript
            wait_time (int): Wait time in seconds for JavaScript to render
            use_readability (bool): Whether to use readability-inspired content extraction

        Returns:
            bool: True if successful, False otherwise
        """
        markdown_content = self.url_to_markdown(
            url, render_js, wait_time, use_readability)

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            print(f"Successfully saved markdown to {output_file}")
            return True
        except Exception as e:
            print(f"Error saving markdown file: {e}")
            return False

    def process_url_batch(self, urls, output_dir="markdown_files", render_js=True, wait_time=None, use_readability=True):
        """
        Process a batch of URLs and save them as Markdown files.

        Args:
            urls (list): List of URLs to process
            output_dir (str): Directory to save the Markdown files
            render_js (bool): Whether to render JavaScript
            wait_time (int): Wait time in seconds for JavaScript to render
            use_readability (bool): Whether to use readability-inspired content extraction

        Returns:
            dict: Dictionary with URLs as keys and success status as values
        """
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        results = {}

        for url in urls:
            try:
                # Create a filename from the URL
                parsed_url = urllib.parse.urlparse(url)
                filename = parsed_url.netloc.replace('.', '_')
                if parsed_url.path and parsed_url.path != '/':
                    path = parsed_url.path.strip('/')
                    # Replace any non-alphanumeric characters with underscores
                    path = re.sub(r'[^a-zA-Z0-9]', '_', path)
                    filename += f"_{path}"

                # Limit filename length and add extension
                filename = filename[:100] + ".md"
                output_file = os.path.join(output_dir, filename)

                # Convert and save
                success = self.save_as_markdown(
                    url, output_file, render_js, wait_time, use_readability)
                results[url] = success

                # Add a random delay between requests to avoid detection
                time.sleep(random.uniform(3, 7))

            except Exception as e:
                print(f"Error processing URL {url}: {e}")
                results[url] = False

        return results

    def rotate_proxy(self, proxy_list=None):
        """
        Setup a rotating proxy for the requests session.

        Args:
            proxy_list (list): List of proxy URLs in format 'http://user:pass@host:port'
                              or 'http://host:port'

        Returns:
            bool: True if proxy was set, False otherwise
        """
        # Example proxy list (replace with your own proxies)
        default_proxies = [
            # Add your proxies here
            # Example: 'http://username:password@proxy.example.com:8080',
            # Example: 'http://123.45.67.89:8080',
        ]

        proxies = proxy_list or default_proxies

        if not proxies:
            print("No proxies available.")
            return False

        try:
            # Select a random proxy
            proxy = random.choice(proxies)

            # If we have a driver, we need to restart it with the new proxy
            if self.driver:
                self.driver.quit()
                self.driver = None

            print(
                f"Using proxy: {proxy.split('@')[-1] if '@' in proxy else proxy}")
            return True
        except Exception as e:
            print(f"Error setting up proxy: {e}")
            return False

    def close(self):
        """Close the WebDriver if it exists."""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def __del__(self):
        """Destructor to ensure the WebDriver is closed."""
        self.close()


# Additional helper methods for improved content extraction

    def _extract_main_content(self, soup):
        """
        Try to extract the main content area of a webpage, filtering out navigation, 
        headers, footers, and sidebar elements.

        Args:
            soup (BeautifulSoup): BeautifulSoup object containing parsed HTML

        Returns:
            BeautifulSoup: Soup object containing only the main content
        """
        # Common content selectors (ordered by priority)
        content_selectors = [
            'main',
            'article',
            '[role="main"]',
            '#content',
            '.content',
            '#main',
            '.main',
            '.post',
            '.entry-content',
            '.post-content'
        ]

        # Try to find the main content area using common selectors
        for selector in content_selectors:
            main_content = soup.select(selector)
            if main_content:
                # Create a new soup with just the main content
                new_soup = BeautifulSoup('<div></div>', 'html.parser')
                main_div = new_soup.div

                # Add each main content element to the new soup
                for content in main_content:
                    main_div.append(content)

                return new_soup

        # If no main content area is found, return the original soup
        # but try to remove headers, footers, navs and other non-content elements
        for element in soup.select('header, footer, nav, aside, .sidebar, [role="navigation"], [role="banner"], [role="complementary"]'):
            element.extract()

        return soup

    def extract_content_with_readability(self, html_content):
        """
        Use readability-inspired heuristics to extract the main content from a webpage.
        This is a simplified approach inspired by the Readability algorithm.

        Args:
            html_content (str): HTML content to process

        Returns:
            str: HTML string containing the extracted main content
        """
        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove elements that usually don't contain content
        for element in soup.select('script, style, iframe, nav, header, footer, form, button, [role="banner"], [role="navigation"], [role="form"]'):
            element.extract()

        # Extract the main content using our helper method
        main_content_soup = self._extract_main_content(soup)

        # Fix relative links in the extracted content
        main_content_soup = self._fix_relative_links(main_content_soup)

        return str(main_content_soup)


# Example usage:
if __name__ == "__main__":
    converter = WebsiteToMarkdown(headless=True)

    # Example 1: Regular website
    url1 = "https://example.com"
    markdown1 = converter.url_to_markdown(url1, render_js=False)
    print(f"Markdown for {url1}:\n{markdown1[:300]}...\n")

    # Example 2: JavaScript-heavy website (e.g., React, Vue)
    url2 = "https://reactjs.org"
    markdown2 = converter.url_to_markdown(url2, render_js=True, wait_time=10)
    print(f"Markdown for {url2}:\n{markdown2[:300]}...\n")

    # Example 3: Using readability to extract main content
    url3 = "https://news.ycombinator.com"
    html_content = converter.fetch_content(url3, render_js=True)
    main_content_html = converter.extract_content_with_readability(
        html_content)
    markdown3 = converter.html_to_markdown(main_content_html)
    print(f"Markdown for {url3} (with readability):\n{markdown3[:300]}...\n")

    # Save to file
    converter.save_as_markdown(url2, "reactjs.md", render_js=True)

    # Always close the driver when done
    converter.close()
