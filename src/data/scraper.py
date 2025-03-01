"""
Web scraper for Canadian university websites.
"""

import os
import sys
import re
import time
import yaml
import requests
from typing import List, Dict, Set, Any, Optional, Tuple
from bs4 import BeautifulSoup
from langchain.schema import Document
from fake_useragent import UserAgent
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import project modules
from src.utils.logger import get_logger, scraper_logger

# Set up logger
logger = get_logger(__name__)

class WebScraper:
    """Web scraper for Canadian university websites."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the scraper with configuration from a YAML file."""
        self.config_path = config_path
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)
        
        # Initialize settings from config
        self.max_depth = self.config['scraping'].get('max_depth', 3)
        self.timeout = self.config['scraping'].get('timeout', 30)
        self.max_pages = self.config['scraping'].get('max_pages', 100)
        self.user_agent_config = self.config['scraping'].get('user_agent', 'random')
        self.max_retries = self.config['scraping'].get('max_retries', 3)
        self.retry_delay = self.config['scraping'].get('retry_delay', 2)
        
        # Information tags for categorization
        self.information_tags = self.config.get('information_tags', [])
        
        # Track already visited URLs
        self.visited_urls: Set[str] = set()
        
        # Track failed URLs for reporting
        self.failed_urls: Dict[str, Dict[str, Any]] = {}
        
        # Initialize user agent
        if self.user_agent_config == 'random':
            self.user_agent = UserAgent()
        else:
            self.user_agent = None
    
    def get_headers(self) -> Dict[str, str]:
        """Get request headers with appropriate user agent."""
        if self.user_agent_config == 'random':
            return {
                'User-Agent': self.user_agent.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        else:
            return {
                'User-Agent': self.user_agent_config,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
    
    def is_valid_url(self, url: str, base_url: str) -> bool:
        """Check if URL is valid for scraping (same domain, not file, etc.)."""
        try:
            # Parse URLs
            parsed_url = urlparse(url)
            parsed_base = urlparse(base_url)
            
            # Check if domain matches
            if parsed_url.netloc != parsed_base.netloc and parsed_url.netloc != '':
                return False
            
            # Skip URLs with file extensions to avoid downloading files
            file_exts = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', 
                        '.zip', '.rar', '.jpg', '.jpeg', '.png', '.gif', '.mp4', '.avi']
            if any(url.lower().endswith(ext) for ext in file_exts):
                return False
            
            # Skip social media links, login, search, and other non-informational pages
            skip_patterns = ['login', 'signin', 'signup', 'search', 'facebook.com', 
                            'twitter.com', 'instagram.com', 'linkedin.com', 'youtube.com']
            if any(pattern in url.lower() for pattern in skip_patterns):
                return False
            
            return True
        except Exception:
            return False
    
    def identify_information_type(self, text: str) -> str:
        """Identify the type of information based on keywords and return as comma-separated string."""
        information_types = []
        text_lower = text.lower()
        
        # The information_tags is a list of dictionaries with 'tag' and 'keywords' keys
        for tag_info in self.information_tags:
            tag = tag_info.get('tag', '')
            keywords = tag_info.get('keywords', [])
            
            if any(keyword.lower() in text_lower for keyword in keywords):
                information_types.append(tag)
        
        # Join the list into a comma-separated string
        return ','.join(information_types)
    
    def extract_content(self, soup: BeautifulSoup, url: str) -> Tuple[str, Dict[str, Any]]:
        """Extract content from a webpage."""
        # Extract title
        title_tag = soup.find('title')
        title = title_tag.text if title_tag else "No Title"
        
        # Remove script, style, and other non-content elements
        for element in soup(['script', 'style', 'nav', 'footer', 'iframe']):
            element.decompose()
        
        # Get main content
        content = soup.get_text(separator=' ', strip=True)
        content = re.sub(r'\s+', ' ', content)  # Remove extra whitespace
        
        # Use the identify_information_type method to get information types as a string
        information_types_str = self.identify_information_type(content + ' ' + title)
        
        # Return content and metadata
        return content, {
            'source': url,
            'title': title,
            'information_types': information_types_str
        }
    
    def fetch_page(self, url: str, retry_count: int = 0) -> Optional[BeautifulSoup]:
        """Fetch a webpage and return BeautifulSoup object with retry logic."""
        try:
            response = requests.get(url, headers=self.get_headers(), timeout=self.timeout)
            
            # Log and track failures
            if response.status_code != 200:
                error_info = {
                    'status_code': response.status_code,
                    'retry_count': retry_count,
                    'timestamp': time.time()
                }
                
                # If this is a 404, try to suggest an alternative
                if response.status_code == 404:
                    # Only suggest alternatives if it's not a retry
                    if retry_count == 0:
                        alternative = self.suggest_alternative_url(url)
                        if alternative:
                            error_info['suggested_alternative'] = alternative
                
                self.failed_urls[url] = error_info
                logger.warning(f"Failed to fetch {url}: HTTP {response.status_code}")
                
                # Retry for specific status codes if we haven't exceeded max retries
                if retry_count < self.max_retries and response.status_code in [429, 500, 503, 504]:
                    # Exponential backoff
                    wait_time = self.retry_delay * (2 ** retry_count)
                    logger.info(f"Retrying {url} in {wait_time} seconds (attempt {retry_count + 1}/{self.max_retries})")
                    time.sleep(wait_time)
                    return self.fetch_page(url, retry_count + 1)
                    
                return None
            
            return BeautifulSoup(response.text, 'html.parser')
        except requests.RequestException as e:
            error_type = type(e).__name__
            logger.error(f"Error fetching {url}: {error_type} - {str(e)}")
            
            self.failed_urls[url] = {
                'error_type': error_type,
                'error_message': str(e),
                'retry_count': retry_count,
                'timestamp': time.time()
            }
            
            # Retry for connection-related errors
            if retry_count < self.max_retries and (
                isinstance(e, (requests.ConnectionError, requests.Timeout))
            ):
                wait_time = self.retry_delay * (2 ** retry_count)
                logger.info(f"Retrying {url} in {wait_time} seconds (attempt {retry_count + 1}/{self.max_retries})")
                time.sleep(wait_time)
                return self.fetch_page(url, retry_count + 1)
                
            return None
    
    def extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract links from a page."""
        links = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            full_url = urljoin(base_url, href)
            if self.is_valid_url(full_url, base_url):
                links.append(full_url)
        return links
    
    def scrape_university(self, university: Dict[str, Any]) -> List[Document]:
        """Scrape a university website and return documents."""
        base_url = university['base_url']
        name = university['name']
        focus_urls = university.get('focus_urls', [base_url])
        
        if not focus_urls:
            focus_urls = [base_url]
        
        print(f"Scraping {name} at {base_url}...")
        documents = []
        self.visited_urls = set()  # Reset visited URLs for each university
        
        # Start with focused URLs
        urls_to_visit = [(url, 0) for url in focus_urls]  # (url, depth)
        pbar = tqdm(total=self.max_pages, desc=f"Scraping {name}")
        
        while urls_to_visit and len(self.visited_urls) < self.max_pages:
            current_url, depth = urls_to_visit.pop(0)
            
            if current_url in self.visited_urls:
                continue
                
            self.visited_urls.add(current_url)
            
            # Fetch and parse the page
            soup = self.fetch_page(current_url)
            if not soup:
                continue
            
            # Extract content and metadata
            content, metadata = self.extract_content(soup, current_url)
            
            # Skip if content is too short (likely not informative)
            if len(content) < 100:
                continue
            
            # Create document
            metadata['university'] = name
            doc = Document(page_content=content, metadata=metadata)
            documents.append(doc)
            
            pbar.update(1)
            
            # If we've reached max depth, don't get more links
            if depth < self.max_depth:
                # Extract links for further crawling
                links = self.extract_links(soup, base_url)
                # Add new links to visit
                for link in links:
                    if link not in self.visited_urls:
                        urls_to_visit.append((link, depth + 1))
            
            # Respect rate limits
            time.sleep(1)
        
        pbar.close()
        print(f"Scraped {len(documents)} pages from {name}")
        return documents
    
    def suggest_alternative_url(self, failed_url: str) -> Optional[str]:
        """Suggest an alternative URL for a failed URL."""
        parsed = urlparse(failed_url)
        base_domain = f"{parsed.scheme}://{parsed.netloc}"
        
        # Common URL patterns to try
        patterns = [
            # Try the base domain
            base_domain,
            # Try removing the last path segment
            '/'.join(failed_url.rstrip('/').split('/')[:-1]),
            # For deep paths, try going up two levels
            '/'.join(failed_url.rstrip('/').split('/')[:-2]) if len(failed_url.split('/')) > 4 else None,
            # Try common alternatives for education sites
            f"{base_domain}/programs",
            f"{base_domain}/academics",
            f"{base_domain}/admissions",
            f"{base_domain}/future-students",
            f"{base_domain}/prospective-students",
        ]
        
        # Filter out None values and the original URL
        patterns = [p for p in patterns if p and p != failed_url]
        
        # Check each pattern
        for alt_url in patterns:
            try:
                logger.debug(f"Checking alternative URL: {alt_url}")
                response = requests.head(alt_url, headers=self.get_headers(), timeout=self.timeout/2)
                if response.status_code == 200:
                    logger.info(f"Found working alternative for {failed_url}: {alt_url}")
                    return alt_url
            except Exception:
                continue
                
        return None

    def check_url_health(self, url: str) -> bool:
        """Check if a URL is healthy (returns 200 OK)."""
        try:
            response = requests.head(url, headers=self.get_headers(), timeout=self.timeout/2)
            return response.status_code == 200
        except Exception:
            return False
    
    def scrape_all_universities(self) -> List[Document]:
        """Scrape all universities defined in the config."""
        all_documents = []
        
        # First, check health of all base_urls and focus_urls
        logger.info("Checking health of all configured URLs")
        with ThreadPoolExecutor(max_workers=10) as executor:
            university_futures = {}
            
            # Submit all base_urls and focus_urls for health check
            for university in self.config['universities']:
                name = university['name']
                base_url = university['base_url']
                focus_urls = university.get('focus_urls', [])
                
                # Check base_url
                future = executor.submit(self.check_url_health, base_url)
                university_futures[(name, base_url, 'base_url')] = future
                
                # Check all focus_urls
                for url in focus_urls:
                    future = executor.submit(self.check_url_health, url)
                    university_futures[(name, url, 'focus_url')] = future
        
            # Process results
            for (name, url, url_type), future in university_futures.items():
                try:
                    is_healthy = future.result()
                    if not is_healthy:
                        logger.warning(f"Unhealthy {url_type} for {name}: {url}")
                        
                        # Try to find an alternative
                        alternative = self.suggest_alternative_url(url)
                        if alternative:
                            logger.info(f"Suggested alternative for {url}: {alternative}")
                            
                            # Record the failed URL
                            self.failed_urls[url] = {
                                'university': name,
                                'url_type': url_type,
                                'suggested_alternative': alternative,
                                'status': 'alternative_found'
                            }
                        else:
                            self.failed_urls[url] = {
                                'university': name,
                                'url_type': url_type,
                                'status': 'no_alternative'
                            }
                except Exception as e:
                    logger.error(f"Error checking {url}: {e}")
        
        # Proceed with scraping
        for university in self.config['universities']:
            documents = self.scrape_university(university)
            all_documents.extend(documents)
        
        # Generate report of failed URLs
        self.generate_failed_urls_report()
        
        print(f"Total documents scraped: {len(all_documents)}")
        return all_documents
    
    def generate_failed_urls_report(self):
        """Generate a report of failed URLs."""
        if not self.failed_urls:
            logger.info("No failed URLs to report")
            return
            
        logger.info(f"Generating report for {len(self.failed_urls)} failed URLs")
        
        # Create report directory if it doesn't exist
        report_dir = os.path.join(os.path.dirname(self.config_path), 'reports')
        os.makedirs(report_dir, exist_ok=True)
        
        # Generate report filename with timestamp
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        report_path = os.path.join(report_dir, f"failed_urls_{timestamp}.yaml")
        
        # Prepare report data
        report_data = {
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'total_failed_urls': len(self.failed_urls),
            'failed_urls': self.failed_urls
        }
        
        # Write report to file
        with open(report_path, 'w') as f:
            yaml.dump(report_data, f, default_flow_style=False)
            
        logger.info(f"Failed URLs report generated at {report_path}")
        print(f"Generated failed URLs report at {report_path}")

if __name__ == "__main__":
    scraper = WebScraper()
    documents = scraper.scrape_all_universities()
    print(f"Scraped {len(documents)} documents in total.") 