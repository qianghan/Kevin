"""
Web scraper for Canadian university websites using spider-py (Python bindings for spider-rs).
Enhanced for better efficiency, performance, and data quality.
"""

import os
import sys
import re
import time
import yaml
import json
import hashlib
import requests
import uuid
import threading
from typing import List, Dict, Set, Any, Optional, Tuple, Callable, Union
from bs4 import BeautifulSoup
from langchain.schema import Document
from urllib.parse import urljoin, urlparse, urlunparse, parse_qs, urlencode
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from datetime import datetime
from pathlib import Path
import unicodedata
import logging
import random
import string
import traceback

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import project modules
from src.utils.logger import get_logger, scraper_logger

# Set up logger
logger = get_logger(__name__)

# Flag to track if spider module is available
SPIDER_AVAILABLE = False
SPIDER_MODULE_NAME = None
SPIDER_RS_ATTRIBUTES = []

# Add SimpleRequestsCrawler as a fallback when no spider module is available
class SimpleRequestsCrawler:
    """Simplified web crawler using requests."""
    
    def __init__(self, max_depth=3, max_retries=3, timeout=30, 
                 allowed_domains=None, include_patterns=None, exclude_patterns=None, 
                 enable_javascript=False, quiet=False):
        """Initialize the crawler with configuration."""
        # Handle the case where a config dictionary is passed instead of individual parameters
        if isinstance(max_depth, dict):
            config = max_depth
            self.max_depth = config.get('max_depth', 3)
            self.max_retries = config.get('max_retries', 3)
            self.timeout = config.get('timeout', 30)
            self.allowed_domains = config.get('allowed_domains', [])
            self.include_patterns = config.get('include_patterns', [])
            self.exclude_patterns = config.get('exclude_patterns', [])
            self.enable_javascript = config.get('enable_javascript', False)
            self.quiet = config.get('quiet', False)
        else:
            # Handle the case where individual parameters are passed
            self.max_depth = max_depth
            self.max_retries = max_retries
            self.timeout = timeout
            self.allowed_domains = allowed_domains or []
            self.include_patterns = include_patterns or []
            self.exclude_patterns = exclude_patterns or []
            self.enable_javascript = enable_javascript
            self.quiet = quiet
            
        self.visited_urls = set()
        self.failed_urls = {}  # Add failed_urls dictionary
        
        # For JavaScript rendering
        self._playwright_browser = None
        
    def _log_info(self, message):
        """Log info messages only if not in quiet mode."""
        if not self.quiet:
            logger.info(message)
    
    def fetch_url(self, url, depth=0, headers=None, retries=0):
        """Fetch a URL and return the content."""
        if url in self.visited_urls:
            return None
            
        headers = headers or {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        self.visited_urls.add(url)
        
        # Generate a request ID for tracing
        req_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        
        try:
            start_time = time.time()
            
            # Decide whether to use Playwright for JavaScript rendering
            if self.enable_javascript:
                self._log_info(f"[REQ-{req_id}] Fetching with JavaScript rendering: {url}")
                content, status_code = self._fetch_with_javascript(url)
                headers = {}  # We don't have easy access to headers with playwright
            else:
                self._log_info(f"SimpleRequestsCrawler: Fetching URL: {url}")
                response = requests.get(
                    url, 
                    headers=headers, 
                    timeout=self.timeout,
                    allow_redirects=True
                )
                content = response.text
                status_code = response.status_code
                headers = dict(response.headers)
            
            elapsed = time.time() - start_time
            self._log_info(f"[REQ-{req_id}] Got response from {url} in {elapsed:.2f}s with status code {status_code}")
            
            if status_code != 200:
                self._log_info(f"[REQ-{req_id}] Non-200 status code: {status_code} for {url}")
                # Still return content for certain status codes that might have useful content
                if status_code in [203, 206, 300, 301, 302, 303, 307, 308]:
                    return {'url': url, 'content': content, 'status_code': status_code, 'headers': headers, 'depth': depth}
                
                # Add to failed URLs
                self.failed_urls[url] = {
                    'error': f"HTTP error {status_code}",
                    'error_type': 'http_error',
                    'timestamp': datetime.now().isoformat()
                }
                return None
                
            return {'url': url, 'content': content, 'status_code': status_code, 'headers': headers, 'depth': depth}
        except Exception as e:
            logger.error(f"[REQ-{req_id}] Error retrieving {url}: {e}")
            # Add to failed URLs
            self.failed_urls[url] = {
                'error': str(e),
                'error_type': type(e).__name__,
                'timestamp': datetime.now().isoformat()
            }
            return None
            
    def crawl(self, base_url, progress_bar=None, max_pages=100):
        """
        Crawl from a base URL and return results.
        
        Args:
            base_url: Starting URL for the crawl
            progress_bar: Optional tqdm progress bar
            max_pages: Maximum number of pages to crawl
            
        Returns:
            List of page results
        """
        self._log_info(f"SimpleRequestsCrawler: Starting crawl from {base_url}")
        
        # Queue of URLs to crawl (URL, depth)
        to_crawl = [(base_url, 0)]
        results = []
        
        if progress_bar:
            progress_bar.total = max_pages
            progress_bar.refresh()
        
        while to_crawl and len(results) < max_pages:
            # Get the next URL to crawl
            url, depth = to_crawl.pop(0)
            
            # Skip if we've already visited or if depth is too high
            if url in self.visited_urls or depth > self.max_depth:
                continue
                
            # Skip if the URL doesn't match allowed domains
            url_domain = urlparse(url).netloc
            if self.allowed_domains and url_domain not in self.allowed_domains:
                continue
                
            # Skip if URL matches exclude patterns
            if any(re.search(pattern, url) for pattern in self.exclude_patterns):
                continue
                
            # Only include if URL matches include patterns (if any are specified)
            if self.include_patterns and not any(re.search(pattern, url) for pattern in self.include_patterns):
                continue
            
            # Fetch the URL
            result = self.fetch_url(url, depth)
            if result:
                # Extract links from the page
                links = self._extract_links(result['content'], url)
                
                # Add page to results
                result['links'] = links
                result['title'] = self._extract_title(result['content'])
                result['text'] = self._extract_text(result['content'])
                result['html'] = result['content']
                
                # Remove the raw content to save memory
                if 'content' in result:
                    del result['content']
                    
                results.append(result)
                
                # Update progress bar
                if progress_bar:
                    progress_bar.update(1)
                    # Only calculate percentage if max_pages is an integer
                    if isinstance(max_pages, int):
                        progress_percentage = int(len(results) / max_pages * 100)
                        progress_bar.set_description(f"Crawling {len(results)}/{max_pages} pages: {progress_percentage}%")
                
                # Queue new links if depth is not too high
                if depth < self.max_depth:
                    for link in links:
                        # Normalize the URL
                        normalized_link = urljoin(url, link)
                        to_crawl.append((normalized_link, depth + 1))
        
        self._log_info(f"SimpleRequestsCrawler: Crawl completed. Scraped {len(results)} pages.")
        return results
        
    def _extract_links(self, html_content, base_url):
        """Extract links from HTML content."""
        links = []
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                if href.startswith('javascript:') or href.startswith('#'):
                    continue
                    
                # Normalize the URL
                absolute_url = urljoin(base_url, href)
                links.append(absolute_url)
        except Exception as e:
            logger.error(f"Error extracting links: {e}")
        
        return links
        
    def _extract_title(self, html_content):
        """Extract page title from HTML content."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            title = soup.title.string if soup.title else ""
            return title.strip()
        except Exception as e:
            logger.error(f"Error extracting title: {e}")
            return ""
            
    def _extract_text(self, html_content):
        """Extract readable text from HTML content."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(['script', 'style']):
                script.extract()
                
            # Get text
            text = soup.get_text()
            
            # Remove excessive newlines and whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return text
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return ""

# Update the spider_rs import logic
try:
    # Try importing spider_rs for the simpler Website API
    import spider_rs
    from spider_rs import Website
    print("Successfully imported spider_rs with Website API")
    SPIDER_AVAILABLE = True
    SPIDER_MODULE_NAME = 'spider_rs'
    
    # Define a function to create a website crawler using the simple spider_rs API
    def create_spider(config):
        # We'll use the simple Website class when available
        # It doesn't take a config dict directly, so we'll handle the conversion
        start_url = config.get('start_url')
        if not start_url:
            # Fix: Ensure max_pages is properly handled when creating SimpleRequestsCrawler
            if isinstance(config, dict) and 'max_pages' in config:
                max_pages_config = config.get('max_pages')
                if isinstance(max_pages_config, dict):
                    logger.warning(f"max_pages is a dictionary: {max_pages_config}. Using default value 100.")
                    config['max_pages'] = 100
                else:
                    try:
                        config['max_pages'] = int(max_pages_config)
                    except (TypeError, ValueError):
                        logger.warning(f"Invalid max_pages value: {max_pages_config}. Using default value 100.")
                        config['max_pages'] = 100
            return SimpleRequestsCrawler(config)
            
        try:
            # Create a Website instance - the Website class in spider_rs doesn't have fluent API methods
            # Instead we need to pass any configuration we need as constructor arguments
            # or access attributes directly
            website = Website(start_url)
            
            # Wrap this in a compatible interface
            class WebsiteWrapper:
                def __init__(self, website, config):
                    self.website = website
                    self.config = config
                    self.failed_urls = {}
                
                def crawl(self, url=None, progress_bar=None):
                    """Crawl the website and return list of results."""
                    logger.info(f"WebsiteWrapper: Starting crawl from {url}")
                    if url is None:
                        url = self.config.get("start_url", "")
                        
                    if not url:
                        raise ValueError("No URL provided for crawl")
                    
                    # Configure website for this crawl
                    max_depth = int(self.config.get("max_depth", 2))
                    
                    # Fix: Ensure max_pages is an integer
                    max_pages_config = self.config.get("max_pages", 100)
                    if isinstance(max_pages_config, dict):
                        logger.warning(f"max_pages is a dictionary: {max_pages_config}. Using default value 100.")
                        max_pages = 100
                    else:
                        try:
                            max_pages = int(max_pages_config)
                        except (TypeError, ValueError):
                            logger.warning(f"Invalid max_pages value: {max_pages_config}. Using default value 100.")
                            max_pages = 100
                    
                    logger.info(f"WebsiteWrapper: max_depth={max_depth}, max_pages={max_pages}")
                    
                    # Add stealth to avoid bot detection
                    self.website.stealth = self.config.get("stealth", True)
                    
                    # Set spider options
                    options = {
                        "respect_robots_txt": self.config.get("respect_robots_txt", True),
                        "max_pages": max_pages,
                        "max_depth": max_depth,
                        "headless": True
                    }
                    
                    # Get allowed domains if any
                    if "allowed_domains" in self.config:
                        options["allowed_domains"] = self.config["allowed_domains"]
                    
                    # Use blacklist if provided
                    if "blacklist_urls" in self.config:
                        options["blacklist_urls"] = self.config["blacklist_urls"]
                    
                    # Set other optional parameters
                    for param in ["timeout", "headers", "proxies", "cookies", "delay"]:
                        if param in self.config:
                            options[param] = self.config[param]
                    
                    # Perform the crawl
                    self.website.crawl(url, **options)
                    crawled_pages = self.website.pages
                    
                    # Count total pages scraped
                    pages_count = len(crawled_pages)
                    
                    # Format results similar to SimpleRequestsCrawler
                    results = []
                    for i, page in enumerate(crawled_pages):
                        if page.status_code >= 400:
                            self.failed_urls[page.url] = {
                                'error': f"HTTP error {page.status_code}",
                                'error_type': 'http_error',
                                'timestamp': datetime.now().isoformat()
                            }
                            continue
                            
                        result = {
                            "url": page.url,
                            "status_code": page.status_code,
                            "title": page.title,
                            "text": page.text,
                            "html": page.html,
                            "headers": page.headers,
                            "links": page.links
                        }
                        results.append(result)
                        
                        # Update progress bar
                        if progress_bar:
                            progress_bar.update(1)
                            # Update progress bar description with current count and percentage
                            if isinstance(pages_count, int) and pages_count > 0:
                                progress_percentage = int((i+1) / pages_count * 100)
                                progress_bar.set_description(f"Crawling {i+1}/{pages_count} pages: {progress_percentage}%")
                        
                        # Print occasional progress updates
                        if (i+1) % 10 == 0:
                            print(f"Currently scraped {i+1} pages", end="\r")
                    
                    logger.info(f"WebsiteWrapper: Crawl completed. Scraped {len(results)} pages.")
                    return results
                
                def get(self, url):
                    """Get a single URL."""
                    try:
                        # In the real spider_rs API, there might not be a get_page method
                        # We need to check if it exists and use a fallback method if not
                        # Trying direct attribute first
                        if hasattr(self.website, 'get_page'):
                            page = self.website.get_page(url)
                            return {
                                "url": page.get("url", url),
                                "status_code": page.get("status_code", 200),
                                "title": page.get("title", ""),
                                "text": page.get("text", ""),
                                "html": page.get("html", ""),
                                "headers": page.get("headers", {}),
                                "content_type": page.get("content_type", "")
                            }
                        else:
                            # Fallback to SimpleRequestsCrawler
                            fallback = SimpleRequestsCrawler(self.config)
                            return fallback.get(url)
                    except Exception as e:
                        print(f"Error in Website.get_page(): {e}")
                        # Fallback to SimpleRequestsCrawler
                        fallback = SimpleRequestsCrawler(self.config)
                        return fallback.get(url)
            
            # Create and return the wrapper
            return WebsiteWrapper(website, config)
        except Exception as e:
            print(f"Error creating spider with Website API: {e}")
            return SimpleRequestsCrawler(config)
            
except ImportError:
    # Try other possible package names for fallbacks
    try:
        import spider
        SPIDER_AVAILABLE = True
        SPIDER_MODULE_NAME = 'spider'
        
        # Define a function to create a spider using the available API
        def create_spider(config):
            try:
                return spider.Spider(config)
            except Exception as e:
                print(f"Error creating spider with spider API: {e}")
                return SimpleRequestsCrawler(config)
                
    except ImportError:
        # Fall back to SimpleRequestsCrawler
        print("No spider libraries found, using SimpleRequestsCrawler")
        SPIDER_AVAILABLE = True  # We'll still mark this as available because we have the fallback
        SPIDER_MODULE_NAME = "requests_fallback"
        
        def create_spider(config):
            return SimpleRequestsCrawler(config)
            
except Exception as e:
    # Catch-all for any other errors during the import process
    print(f"Error setting up web scraping system: {e}")
    print("Falling back to SimpleRequestsCrawler")
    
    SPIDER_AVAILABLE = True  # We'll mark this as available because we have the fallback
    SPIDER_MODULE_NAME = "requests_fallback"
    
    def create_spider(config):
        return SimpleRequestsCrawler(config)

# Log the status of spider module
logger.info(f"Web scraping using {SPIDER_MODULE_NAME}")
print(f"Web scraping using {SPIDER_MODULE_NAME}")

class UniversitySpider:
    """Enhanced web crawler for university websites using spider-py."""
    
    def __init__(self, config: Dict[str, Any], cache_dir: str = None):
        """Initialize the spider with configuration."""
        self.config = config
        self.visited_urls: Set[str] = set()
        self.failed_urls: Dict[str, Dict[str, Any]] = {}
        self.content_cache: Dict[str, Dict[str, Any]] = {}
        self.content_hashes: Set[str] = set()  # For deduplication
        
        # Initialize configuration variables
        self.timeout = config.get('timeout', 30)
        self.max_retries = config.get('max_retries', 3)
        self.retry_delay = config.get('retry_delay', 2)
        self.max_depth = config.get('max_depth', 3)
        self.enable_javascript = config.get('enable_javascript', False)
        self.user_agent = config.get('user_agent', 'random')
        
        # Handle max_pages properly
        max_pages_config = config.get('max_pages', 100)
        if isinstance(max_pages_config, dict):
            logger.warning(f"max_pages is a dictionary: {max_pages_config}. Using default value 100.")
            self.max_pages = 100
        else:
            try:
                self.max_pages = int(max_pages_config)
            except (TypeError, ValueError):
                logger.warning(f"Invalid max_pages value: {max_pages_config}. Using default value 100.")
                self.max_pages = 100
            
        # Get block patterns from config
        self.block_patterns = config.get('block_patterns', [])
        # Also check if it's in the scraping section
        if 'scraping' in config and 'block_patterns' in config['scraping']:
            self.block_patterns = config['scraping']['block_patterns']
        
        # Initialize timing limits
        self.max_crawl_duration = config.get('max_crawl_duration', 600)  # 10 minutes default
        self.max_url_processing_time = config.get('max_url_processing_time', 60)  # 1 minute default
        self.enable_emergency_exit = config.get('enable_emergency_exit', False)
        
        # Configure cache
        self.cache_dir = cache_dir
        if self.cache_dir:
            os.makedirs(self.cache_dir, exist_ok=True)
            logger.info(f"Using cache directory: {self.cache_dir}")
        
        logger.info(f"Initialized UniversitySpider with timeout {self.timeout}s, max depth {self.max_depth}, " +
                    f"max retries {self.max_retries}, retry delay {self.retry_delay}s, " +
                    f"max crawl duration {self.max_crawl_duration}s, " +
                    f"max URL processing time {self.max_url_processing_time}s, emergency exit: {self.enable_emergency_exit}")
    
    def _log(self, message, quiet_mode=False):
        """Log a message unless in quiet mode."""
        if not quiet_mode:
            logger.info(message)
    
    def get_cache_path(self, url: str) -> str:
        """Generate a cache file path for a URL."""
        if not self.cache_dir:
            return None
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{url_hash}.json")
    
    def load_from_cache(self, url: str) -> Optional[Dict[str, Any]]:
        """Load page data from cache if available."""
        if not self.cache_dir:
            return None
            
        cache_path = self.get_cache_path(url)
        if cache_path and os.path.exists(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    data = json.load(f)
                    
                # Check cache expiry (default 7 days)
                if 'cached_at' in data:
                    cache_time = datetime.fromisoformat(data['cached_at'])
                    now = datetime.now()
                    cache_age = (now - cache_time).total_seconds()
                    max_age = self.config.get('cache_max_age', 7 * 24 * 60 * 60)  # 7 days in seconds
                    
                    if cache_age > max_age:
                        logger.debug(f"Cache expired for {url}")
                        return None
                
                logger.debug(f"Loaded from cache: {url}")
                return data
            except Exception as e:
                logger.warning(f"Error loading cache for {url}: {e}")
        
        return None
    
    def save_to_cache(self, url: str, data: Dict[str, Any]):
        """Save page data to cache."""
        if not self.cache_dir:
            return
            
        cache_path = self.get_cache_path(url)
        if cache_path:
            try:
                # Add cache timestamp
                data_to_cache = dict(data)
                data_to_cache['cached_at'] = datetime.now().isoformat()
                
                with open(cache_path, 'w') as f:
                    json.dump(data_to_cache, f)
                logger.debug(f"Saved to cache: {url}")
            except Exception as e:
                logger.warning(f"Error saving cache for {url}: {e}")
    
    def is_duplicate_content(self, content: str) -> bool:
        """Check if content is a duplicate based on content hash."""
        if not content or len(content) < 100:
            return False
            
        # Create a hash of the content
        content_sample = content[:1000]  # Use first 1000 chars for faster comparison
        content_hash = hashlib.md5(content_sample.encode()).hexdigest()
        
        if content_hash in self.content_hashes:
            return True
            
        self.content_hashes.add(content_hash)
        return False
    
    def crawl(self, base_url: str, focus_urls: List[str], 
              content_processor: Callable[[Dict[str, Any], str], Tuple[str, Dict[str, Any]]]) -> List[Document]:
        """
        Crawl university website and process content.
        
        Args:
            base_url: Base domain URL
            focus_urls: List of starting URLs
            content_processor: Function to process raw content into document
            
        Returns:
            List of Document objects
        """
        crawl_id = str(uuid.uuid4())[:8]
        # Check for quiet mode in config
        quiet_mode = self.config.get('quiet', False)
        
        # Use _log method instead of directly calling logger
        self._log(f"[MAIN-{crawl_id}] Starting UniversitySpider.crawl for base_url: {base_url}", quiet_mode)
        if not focus_urls:
            focus_urls = [base_url]
            self._log(f"[MAIN-{crawl_id}] No focus URLs provided, using base_url: {base_url}", quiet_mode)
            
        # Configure spider settings
        crawler_config = dict(self.config.get('spider_config', {}))
        allowed_domains = [urlparse(base_url).netloc]
        crawler_config["allowed_domains"] = allowed_domains
        self._log(f"[MAIN-{crawl_id}] Allowed domains: {allowed_domains}", quiet_mode)
        
        # Add university-specific block patterns
        block_patterns = self.block_patterns
        crawler_config["blacklist_urls"] = [
            re.compile(pattern) for pattern in block_patterns
        ]
        if not quiet_mode:
            logger.debug(f"[MAIN-{crawl_id}] Added {len(block_patterns)} block patterns")
        
        # Initialize spider with smart settings
        crawler_config.update({
            "smart_crawl": True,  # Enable smart crawling mode for better content discovery
            "stealth": True,  # Enable stealth mode to avoid bot detection
            "content_similarity_threshold": 0.7,  # Avoid near-duplicate content
            "respect_robots_txt": True,
            "extract_text": True,
            "extract_metadata": True,
            "cache_enabled": bool(self.cache_dir),
            "js_enabled": self.enable_javascript,
            "timeout": self.timeout,  # Add timeout to configuration
            "max_url_processing_time": self.max_url_processing_time,  # Add URL processing timeout
            "quiet": quiet_mode,  # Pass quiet mode to crawler
        })
        
        # Create output documents list
        documents = []
        university_name = self.config.get('university_name', 'Unknown University')
        self._log(f"[MAIN-{crawl_id}] Crawling for university: {university_name}", quiet_mode)
        
        # Set up progress tracking
        max_pages = self.max_pages  # Use the pre-validated value
        self._log(f"[MAIN-{crawl_id}] Maximum pages to crawl: {max_pages}", quiet_mode)
        # Initialize progress bar with better positioning and format
        pbar = tqdm(total=max_pages, desc=f"Crawling {university_name}", 
                   bar_format='{l_bar}{bar:30}{r_bar}{bar:-30b}', 
                   position=0, leave=True)
        
        # Add a counter for real-time updates
        pages_scraped_counter = 0
        
        # Function to update the progress bar description to show current count
        def update_progress(count):
            nonlocal pages_scraped_counter
            pages_scraped_counter = count
            pbar.set_description(f"Crawling {university_name}: {count}/{max_pages}")
            
        # Track focus URLs status
        focus_urls_status = {url: "pending" for url in focus_urls}
        completed_focus_urls = 0
        
        # Track overall crawl start time for deadlock detection
        crawl_start_time = time.time()
        
        # Store the last activity timestamp to detect no-progress situations
        last_activity_time = time.time()
        activity_timeout = max(self.timeout * 3, 180)  # Default to at least 3 minutes
        
        # Add a heartbeat logger to detect hanging even during long-running operations
        def log_heartbeat():
            nonlocal last_activity_time
            current_time = time.time()
            
            elapsed = current_time - crawl_start_time
            no_activity_time = current_time - last_activity_time
            
            logger.info(f"[MAIN-{crawl_id}] Crawl heartbeat: Running for {elapsed:.2f}s, " +
                       f"last activity: {no_activity_time:.2f}s ago, " +
                       f"completed {len(documents)}/{max_pages} documents")
            
            # Check if we've exceeded the maximum crawl duration
            if elapsed > self.max_crawl_duration:
                logger.error(f"[MAIN-{crawl_id}] CRITICAL: Maximum crawl duration ({self.max_crawl_duration}s) exceeded. Deadlock detected.")
                if self.enable_emergency_exit:
                    logger.critical(f"[MAIN-{crawl_id}] EMERGENCY EXIT: Forcing process termination due to deadlock")
                    # Use os._exit for an immediate, non-graceful shutdown as a last resort
                    # This is drastic but necessary for truly stuck processes
                    os._exit(1)
                
            # Check for extended periods of no activity (no new documents added)
            if no_activity_time > activity_timeout:
                logger.warning(f"[MAIN-{crawl_id}] No activity detected for {no_activity_time:.2f}s (timeout: {activity_timeout}s)")
                if no_activity_time > activity_timeout * 2:
                    logger.error(f"[MAIN-{crawl_id}] CRITICAL: No activity for {no_activity_time:.2f}s, possibly hung")
                    if self.enable_emergency_exit:
                        logger.critical(f"[MAIN-{crawl_id}] EMERGENCY EXIT: Forcing process termination due to inactivity")
                        # Use os._exit for an immediate, non-graceful shutdown as a last resort
                        os._exit(2)
        
        # Schedule heartbeat logs every minute
        heartbeat_interval = 30  # seconds - reduced to increase checking frequency
        heartbeat_timer = None
        
        def schedule_next_heartbeat():
            nonlocal heartbeat_timer
            if heartbeat_timer:
                try:
                    heartbeat_timer.cancel()
                except:
                    pass
            heartbeat_timer = threading.Timer(heartbeat_interval, run_heartbeat)
            heartbeat_timer.daemon = True
            heartbeat_timer.start()
        
        def run_heartbeat():
            try:
                log_heartbeat()
                schedule_next_heartbeat()
            except Exception as e:
                logger.error(f"[MAIN-{crawl_id}] Error in heartbeat: {e}")
        
        # Start the heartbeat timer
        schedule_next_heartbeat()
        
        try:
            # Fix: Define content_processor function if missing
            if not hasattr(self, 'extract_content_from_spider_result'):
                # Define a basic content processor function
                def extract_content_from_spider_result(result, url):
                    """Extract and process content from a spider result.
                    
                    Args:
                        result: The raw result from the spider crawl
                        url: The URL of the page
                        
                    Returns:
                        Tuple of (content, metadata)
                    """
                    try:
                        # Extract basic content
                        content = result.get('text', '')
                        title = result.get('title', '')
                        
                        # Skip if content is too short
                        if not content or len(content) < 100:
                            logger.debug(f"Skipping {url} - content too short ({len(content) if content else 0} chars)")
                            return '', {}
                            
                        # Extract metadata
                        metadata = {
                            'source': url,
                            'title': title,
                            'content_type': result.get('content_type', ''),
                            'status_code': result.get('status_code', 0),
                            'headers': result.get('headers', {}),
                            'university': result.get('university_name', 'Unknown University')
                        }
                        
                        # Add timestamp
                        metadata['scraped_at'] = datetime.now().isoformat()
                        
                        return content, metadata
                        
                    except Exception as e:
                        logger.error(f"Error extracting content from {url}: {e}")
                        return '', {}
                    
                self.extract_content_from_spider_result = extract_content_from_spider_result
            
            # Initialize the crawler with our configuration
            # Using the create_spider function defined in this file
            
            # Setup spider configuration
            spider_config = {
                'max_depth': self.max_depth,
                'timeout': self.timeout,
                'max_retries': self.max_retries,
                'retry_delay': self.retry_delay,
                'enable_javascript': self.enable_javascript,
                'user_agent': self.user_agent,
                'block_patterns': block_patterns if block_patterns else [],
                'university_name': university_name,
                'max_crawl_duration': self.max_crawl_duration,
                'max_url_processing_time': self.max_url_processing_time,
                'enable_emergency_exit': self.enable_emergency_exit,
                'max_pages': max_pages,  # Use the pre-validated value
            }
            
            # Create the crawler
            crawler = create_spider(spider_config)
            
            # Initialize documents list
            documents = []
            
            # Process each focus URL
            for focus_url in focus_urls:
                logger.info(f"Crawling focus URL: {focus_url}")
                try:
                    # Call the crawl method with the correct parameters
                    results = crawler.crawl(focus_url, pbar)
                    
                    # Process the results
                    for result in results:
                        content, metadata = self.extract_content_from_spider_result(result, result.get('url', ''))
                        if content and len(content) > 100:
                            metadata['university'] = university_name
                            doc = Document(page_content=content, metadata=metadata)
                            documents.append(doc)
                            
                            # Update the progress counter and display
                            update_progress(len(documents))
                            
                            # Print regular updates to console
                            if len(documents) % 10 == 0:
                                print(f"Currently scraped {len(documents)}/{max_pages} pages from {university_name}", end="\r")
                            
                            # Check if we've reached the maximum number of pages
                            if len(documents) >= max_pages:
                                logger.info(f"Reached maximum pages limit ({max_pages})")
                                break
                    
                    # Check if we've reached the maximum number of pages
                    if len(documents) >= max_pages:
                        break
                        
                except Exception as e:
                    logger.error(f"Error crawling {focus_url}: {e}")
                    self.failed_urls[focus_url] = {
                        'error': str(e),
                        'error_type': type(e).__name__,
                        'timestamp': datetime.now().isoformat()
                    }
            
            crawl_duration = time.time() - crawl_start_time
            logger.info(f"Crawl completed in {crawl_duration:.2f} seconds")
            
            # Update failed URLs tracking
            self.failed_urls.update(crawler.failed_urls)
            
            # Log results
            print(f"\nScraped {len(documents)} pages from {university_name}")
            logger.info(f"Scraped {len(documents)} pages from {university_name}")
            
            if crawler.failed_urls:
                print(f"  Failed URLs: {len(crawler.failed_urls)}")
                logger.warning(f"Failed URLs: {len(crawler.failed_urls)}")
                for url, error in list(crawler.failed_urls.items())[:5]:  # Log first 5 failures
                    logger.warning(f"  - {url}: {error['error']}")
            
            logger.info(f"========== COMPLETED SCRAPE FOR {university_name} ==========")
            
            # Close the progress bar to prevent display issues
            pbar.close()
            
            return documents
            
        finally:
            # Always clean up the heartbeat timer
            if heartbeat_timer:
                try:
                    heartbeat_timer.cancel()
                except:
                    pass
                    
            # Ensure progress bar is closed
            try:
                pbar.close()
            except:
                pass

class UniversityContentExtractor:
    """Specialized content extractor for university websites."""
    
    # Information categories for university content
    CATEGORIES = {
        'admission': ['admission', 'apply', 'application', 'requirements', 'how to apply', 'applicant', 'entrance'],
        'tuition': ['tuition', 'fees', 'cost', 'financial', 'scholarships', 'bursaries', 'aid', 'funding'],
        'programs': ['programs', 'degrees', 'majors', 'minors', 'courses', 'curriculum', 'faculty', 'department'],
        'faculty': ['faculty', 'professor', 'instructor', 'dean', 'chair', 'research', 'academic staff'],
        'student_life': ['student life', 'campus', 'housing', 'residence', 'dorm', 'activities', 'clubs'],
        'contact': ['contact', 'email', 'phone', 'address', 'location', 'directory', 'connect'],
        'deadlines': ['deadline', 'dates', 'calendar', 'schedule', 'important dates', 'academic calendar'],
        'international': ['international', 'abroad', 'foreign', 'exchange', 'global', 'overseas'],
        'graduate': ['graduate', 'master', 'phd', 'doctorate', 'postgraduate', 'research program']
    }
    
    # Common page types to prioritize
    PAGE_TYPES = {
        'admission_page': re.compile(r'.*(admission|apply|application).*', re.IGNORECASE),
        'program_page': re.compile(r'.*(program|degree|major|faculty|department).*', re.IGNORECASE),
        'tuition_page': re.compile(r'.*(tuition|fee|cost|financial).*', re.IGNORECASE),
        'international_page': re.compile(r'.*(international|foreign|abroad).*', re.IGNORECASE),
        'faculty_page': re.compile(r'.*(faculty|professor|instructor|staff|research).*', re.IGNORECASE),
        'contact_page': re.compile(r'.*(contact|directory|connect).*', re.IGNORECASE),
        'deadline_page': re.compile(r'.*(deadline|date|calendar|schedule).*', re.IGNORECASE)
    }
    
    def __init__(self):
        """Initialize the content extractor."""
        # Patterns for specific information extraction
        self.patterns = {
            'email': re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
            'phone': re.compile(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'),
            'tuition_pattern': re.compile(r'\$\s?[\d,]+(\.\d{2})?|\d{1,3}(,\d{3})*(\.\d{2})?\s(dollars|CAD|CDN)'),
            'deadline_pattern': re.compile(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(st|nd|rd|th)?,\s+\d{4}|\d{1,2}(st|nd|rd|th)?\s+(January|February|March|April|May|June|July|August|September|October|November|December),\s+\d{4}')
        }
    
    def categorize_content(self, text: str, url: str) -> List[str]:
        """Categorize content by type of university information."""
        text = text.lower()
        url_lower = url.lower()
        categories = []
        
        # Check URL patterns first - often very reliable indicators
        for category, keywords in self.CATEGORIES.items():
            if any(keyword in url_lower for keyword in keywords):
                categories.append(category)
        
        # If nothing found in URL, check content
        if not categories:
            for category, keywords in self.CATEGORIES.items():
                if any(keyword in text for keyword in keywords):
                    categories.append(category)
        
        # Check for specific page types
        for page_type, pattern in self.PAGE_TYPES.items():
            if pattern.search(url_lower) or pattern.search(text):
                categories.append(page_type.replace('_page', ''))
        
        return list(set(categories))  # Remove duplicates
    
    def identify_page_type(self, url: str, title: str, content: str) -> str:
        """Identify the type of university page for better content organization."""
        url_lower = url.lower()
        title_lower = title.lower()
        
        # Check URL and title first
        for page_type, pattern in self.PAGE_TYPES.items():
            if pattern.search(url_lower) or pattern.search(title_lower):
                return page_type
        
        # If not found, check content
        for page_type, pattern in self.PAGE_TYPES.items():
            if pattern.search(content[:1000]):  # Only check beginning of content
                return page_type
        
        return "general"
    
    def extract_structured_data(self, html: str, url: str) -> Dict[str, Any]:
        """Extract structured data from HTML content."""
        structured_data = {}
        
        if not html:
            return structured_data
            
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract emails
            emails = set(self.patterns['email'].findall(html))
            if emails:
                structured_data['emails'] = list(emails)
            
            # Extract phone numbers
            phones = set(self.patterns['phone'].findall(html))
            if phones:
                structured_data['phones'] = list(phones)
            
            # Extract tuition information
            tuition_text = ""
            tuition_elements = soup.find_all(string=self.patterns['tuition_pattern'])
            for element in tuition_elements:
                parent = element.parent
                if parent:
                    context = parent.get_text(strip=True)
                    tuition_text += context + "\n"
            
            if tuition_text:
                structured_data['tuition_info'] = tuition_text
            
            # Extract deadline information
            deadline_text = ""
            deadline_elements = soup.find_all(string=self.patterns['deadline_pattern'])
            for element in deadline_elements:
                parent = element.parent
                if parent:
                    context = parent.get_text(strip=True)
                    deadline_text += context + "\n"
            
            if deadline_text:
                structured_data['deadline_info'] = deadline_text
            
            # Extract tables - often contain important structured information
            tables = []
            for table in soup.find_all('table'):
                try:
                    # Get table headers
                    headers = []
                    for th in table.find_all('th'):
                        headers.append(th.get_text(strip=True))
                    
                    # Get table rows
                    rows = []
                    for tr in table.find_all('tr'):
                        row = []
                        for td in tr.find_all(['td', 'th']):
                            row.append(td.get_text(strip=True))
                        if row:
                            rows.append(row)
                    
                    if rows:
                        tables.append({
                            'headers': headers,
                            'rows': rows
                        })
                except Exception:
                    continue
            
            if tables:
                structured_data['tables'] = tables
                
            # Extract lists - often contain program requirements or tuition breakdowns
            lists = []
            for list_element in soup.find_all(['ul', 'ol']):
                # Avoid navigation menus
                if list_element.find_parent(['nav', 'header', 'footer']):
                    continue
                    
                # Get list items
                items = []
                for li in list_element.find_all('li'):
                    text = li.get_text(strip=True)
                    if text and len(text) > 10:  # Skip very short list items
                        items.append(text)
                
                if items and len(items) > 1:  # At least 2 items
                    lists.append(items)
            
            if lists:
                structured_data['lists'] = lists
            
        except Exception as e:
            pass
            
        return structured_data
    
    def extract_content_by_section(self, html: str) -> Dict[str, str]:
        """Extract content by section for better chunking and relevance."""
        sections = {}
        
        if not html:
            return sections
            
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Process headings to identify sections
            current_section = "main"
            sections[current_section] = ""
            
            # Track all content elements in order
            elements = []
            for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div', 'section']):
                # Skip hidden elements
                style = element.get('style', '')
                if 'display: none' in style or 'visibility: hidden' in style:
                    continue
                    
                tag_name = element.name
                
                # Create a new section for headings
                if tag_name.startswith('h') and len(element.get_text(strip=True)) > 0:
                    level = int(tag_name[1])
                    heading_text = element.get_text(strip=True)
                    if len(heading_text) > 3:  # Skip very short headings
                        current_section = heading_text
                        sections[current_section] = ""
                        elements.append((current_section, None))  # Mark as a heading
                elif tag_name in ['p', 'div', 'section']:
                    content = element.get_text(strip=True)
                    # Only include non-empty content that's reasonably long
                    if content and len(content) > 20:
                        elements.append((current_section, content))
            
            # Consolidate content within each section
            for section_name, content in elements:
                if content is None:  # It's a heading
                    continue
                
                if section_name in sections:
                    sections[section_name] += content + " "
                else:
                    sections[section_name] = content + " "
            
            # Clean up sections
            for section_name in list(sections.keys()):
                sections[section_name] = sections[section_name].strip()
                # Remove any empty sections
                if not sections[section_name]:
                    del sections[section_name]
                    
        except Exception as e:
            pass
            
        return sections

def _normalize_string(text: str) -> str:
    """
    Normalize a string for use as a filename or directory name.
    
    Args:
        text: The string to normalize
        
    Returns:
        Normalized string with only alphanumeric characters and underscores
    """
    # Remove accents and normalize the string
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
    
    # Replace spaces and special characters with underscores
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    text = re.sub(r'[-\s]+', '_', text)
    
    return text

class WebScraper:
    """Main web scraper class for university websites."""
    
    def __init__(self, config_path: str, max_pages: int = None, quiet: bool = False):
        """
        Initialize the web scraper with the given configuration.
        
        Args:
            config_path: Path to configuration file
            max_pages: Maximum pages to scrape per university
            quiet: Whether to suppress INFO level logs
        """
        try:
            self.config_path = config_path
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
                
            # Initialize attributes
            max_pages_config = max_pages or self.config['scraping'].get('max_pages', 100)
            # Ensure max_pages is an integer
            if isinstance(max_pages_config, dict):
                logger.warning(f"max_pages is a dictionary: {max_pages_config}. Using default value 100.")
                self.max_pages = 100
            else:
                try:
                    self.max_pages = int(max_pages_config)
                except (TypeError, ValueError):
                    logger.warning(f"Invalid max_pages value: {max_pages_config}. Using default value 100.")
                    self.max_pages = 100
                    
            self.quiet = quiet
            self.failed_urls = {}
            
            # Setup cache directory
            self.cache_dir = os.path.join(os.path.dirname(config_path), self.config['scraping'].get('cache_dir', 'cache'))
            os.makedirs(self.cache_dir, exist_ok=True)
            
            # Get content types if specified
            self.content_types = self.config['scraping'].get('content_types', [])
            
            # Timeout for requests
            self.timeout = self.config['scraping'].get('timeout', 30)
            
            # Setup block patterns
            self.block_patterns = self.config['scraping'].get('block_patterns', [])
            
            # Setup spider configuration
            self.spider_config = self.config['scraping'].get('spider_config', {})
            self.spider_config['max_pages'] = self.max_pages  # Use the validated max_pages value
            self.spider_config['quiet'] = quiet  # Add quiet flag to spider config
            
        except Exception as e:
            logger.error(f"Error initializing WebScraper: {e}")
            logger.error(traceback.format_exc())
            raise
            
    def scrape_university(self, university_config: Dict[str, Any], mode: str = "cache_first") -> List[Document]:
        """
        Scrape a specific university based on configuration.
        
        Args:
            university_config: University configuration dictionary
            mode: Scraping mode (cache_first, force_scrape, mock)
            
        Returns:
            List of Document objects
        """
        # Check if we're in quiet mode
        quiet_mode = self.spider_config.get('quiet', False)
        
        university_name = university_config.get('name', 'Unknown University')
        if not quiet_mode:
            logger.info(f"Starting scrape for university: {university_name}")
        
        # Create cache directory for university
        cache_dir = os.path.join(self.cache_dir, _normalize_string(university_name))
        os.makedirs(cache_dir, exist_ok=True)
        
        # Extract base URL and focus URLs for the university
        base_url = university_config.get('base_url', None)
        if not base_url:
            if not quiet_mode:
                logger.warning(f"No base URL found for {university_name}, skipping")
            return []
        
        # Get focus URLs (specific URLs to crawl)
        focus_urls = []
        if 'focus_urls' in university_config and university_config['focus_urls']:
            focus_urls = university_config['focus_urls']
            if not quiet_mode:
                logger.info(f"Using {len(focus_urls)} focus URLs for {university_name}")
        
        # Add block patterns from university config
        block_patterns = list(self.block_patterns)
        if 'block_patterns' in university_config and university_config['block_patterns']:
            block_patterns.extend(university_config['block_patterns'])
        
        # Create university-specific config for the spider
        university_config_copy = university_config.copy()
        university_config_copy.update({
            'university_name': university_name,
            'spider_config': self.spider_config.copy(),
            'block_patterns': block_patterns,
            'max_pages': self.max_pages,  # Set max pages from WebScraper (already validated)
            'quiet': quiet_mode,  # Pass quiet mode to the spider
        })
        
        # Add content types to spider config if set
        if self.content_types:
            university_config_copy['content_types'] = self.content_types
        
        # Initialize the spider
        spider = UniversitySpider(university_config_copy, cache_dir)
        
        # Extract content from scraped pages
        documents = []
        try:
            # Create a content extractor
            content_extractor = UniversityContentExtractor()
            
            # Start the crawl
            if not quiet_mode:
                logger.info(f"Starting crawl for {university_name} with base URL: {base_url}")
            
            # Wrap the content extraction function to pass to the crawler
            def process_content(result, source_url):
                return self._extract_content_from_spider_result(result, university_name, content_extractor)
            
            # Run the crawl and get documents
            documents = spider.crawl(base_url, focus_urls, process_content)
            
            # Log results
            failed_urls_count = len(spider.failed_urls)
            if not quiet_mode:
                logger.info(f"Crawl for {university_name} completed. Collected {len(documents)} pages.")
                if failed_urls_count > 0:
                    logger.warning(f"Failed to crawl {failed_urls_count} URLs for {university_name}")
            
            # Track the failed URLs for later analysis
            self.failed_urls.update(spider.failed_urls)
            
            return documents
            
        except Exception as e:
            logger.error(f"Error scraping {university_name}: {e}")
            logger.error(traceback.format_exc())
            return []
            
    def _extract_content_from_spider_result(self, result, university_name, extractor=None):
        """
        Extract and process content from a spider result.
        
        Args:
            result: The raw result from the spider crawl
            university_name: Name of the university being scraped
            extractor: Optional content extractor instance
            
        Returns:
            Tuple of (content, metadata)
        """
        try:
            # Extract basic content
            content = result.get('text', '')
            title = result.get('title', '')
            url = result.get('url', '')
            
            # Skip if content is too short
            if not content or len(content) < 100:
                if not self.quiet:
                    logger.debug(f"Skipping {url} - content too short ({len(content) if content else 0} chars)")
                return '', {}
            
            # Extract metadata
            metadata = {
                'source': url,
                'title': title,
                'content_type': result.get('content_type', ''),
                'status_code': result.get('status_code', 0),
                'headers': result.get('headers', {}),
                'university': university_name
            }
            
            # Add timestamp
            metadata['scraped_at'] = datetime.now().isoformat()
            
            # If extractor is provided, use it for additional processing
            if extractor:
                # Categorize content
                categories = extractor.categorize_content(content, url)
                if categories:
                    metadata['content_categories'] = categories
                
                # Extract structured data if HTML is available
                if 'html' in result:
                    structured_data = extractor.extract_structured_data(result['html'], url)
                    if structured_data:
                        metadata['structured_data'] = structured_data
                
                # Extract content by section
                if 'html' in result:
                    sections = extractor.extract_content_by_section(result['html'])
                    if sections:
                        metadata['sections'] = list(sections.keys())
            
            return content, metadata
            
        except Exception as e:
            if not self.quiet:
                logger.error(f"Error extracting content: {e}")
            return '', {}
            
    def scrape_all_universities(self) -> List[Document]:
        """
        Scrape all universities defined in the configuration.
        
        Returns:
            List of Document objects
        """
        all_documents = []
        
        # Create a master progress bar for all universities
        total_universities = len(self.config['universities'])
        
        # Only show detailed message if not in quiet mode
        if not self.quiet:
            logger.info(f"Starting scrape of {total_universities} universities")
        
        # Display progress bar
        master_pbar = tqdm(
            total=total_universities, 
            desc="Universities Processed", 
            position=0, 
            leave=True,
            bar_format='{l_bar}{bar:30}{r_bar}{bar:-30b}'
        )
        
        # Track total documents scraped
        total_docs_scraped = 0
        
        # Process each university
        for university in self.config['universities']:
            university_name = university.get('name', 'Unknown University')
            master_pbar.set_description(f"Processing: {university_name}")
            
            # Scrape the university
            documents = self.scrape_university(university)
            
            # Track documents
            docs_count = len(documents)
            all_documents.extend(documents)
            total_docs_scraped += docs_count
            
            # Update progress bar
            master_pbar.update(1)
            master_pbar.set_description(f"Universities: {master_pbar.n}/{total_universities} (Total docs: {total_docs_scraped})")
        
        # Close progress bar
        master_pbar.close()
        
        # Only show detailed message if not in quiet mode
        if not self.quiet:
            logger.info(f"Scraping complete! Total documents scraped: {len(all_documents)}")
        
        return all_documents

if __name__ == "__main__":
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Run the enhanced web scraper')
    parser.add_argument('--config', default='config.yaml', help='Path to configuration file')
    parser.add_argument('--university', help='Scrape a specific university by name')
    parser.add_argument('--max-pages', type=int, help='Maximum pages to scrape per university')
    parser.add_argument('--no-cache', action='store_true', help='Disable caching')
    parser.add_argument('--js', action='store_true', help='Enable JavaScript rendering')
    args = parser.parse_args()
    
    # Create scraper with config
    scraper = WebScraper(config_path=args.config)
    
    # Apply command line overrides
    if args.max_pages:
        scraper.max_pages = args.max_pages
        scraper.spider_config['max_pages'] = args.max_pages
    
    if args.no_cache:
        scraper.cache_enabled = False
        scraper.cache_dir = None
    
    if args.js:
        scraper.enable_javascript = True
        scraper.spider_config['js_enabled'] = True
    
    # Scrape specific university or all
    start_time = time.time()
    if args.university:
        found = False
        for university in scraper.config['universities']:
            if university['name'].lower() == args.university.lower():
                documents = scraper.scrape_university(university)
                found = True
                break
        
        if not found:
            print(f"University '{args.university}' not found in configuration")
            sys.exit(1)
    else:
        documents = scraper.scrape_all_universities()
    
    # Print timing information
    elapsed = time.time() - start_time
    print(f"Scraped {len(documents)} documents in {elapsed:.2f} seconds ({len(documents)/elapsed:.2f} docs/sec)") 