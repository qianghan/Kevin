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

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import project modules
from src.utils.logger import get_logger, scraper_logger

class WebScraper:
    """Web scraper for Canadian university websites."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the scraper with configuration from a YAML file."""
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)
        
        # Initialize settings from config
        self.max_depth = self.config['scraping'].get('max_depth', 3)
        self.timeout = self.config['scraping'].get('timeout', 30)
        self.max_pages = self.config['scraping'].get('max_pages', 100)
        self.user_agent_config = self.config['scraping'].get('user_agent', 'random')
        
        # Information tags for categorization
        self.information_tags = self.config.get('information_tags', [])
        
        # Track already visited URLs
        self.visited_urls: Set[str] = set()
        
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
    
    def identify_information_type(self, text: str) -> List[str]:
        """Identify the type of information based on keywords."""
        information_types = []
        text_lower = text.lower()
        
        for tag_info in self.information_tags:
            tag = tag_info.get('tag', '')
            keywords = tag_info.get('keywords', [])
            
            if any(keyword.lower() in text_lower for keyword in keywords):
                information_types.append(tag)
        
        return information_types
    
    def extract_content(self, soup: BeautifulSoup, url: str) -> Tuple[str, Dict[str, Any]]:
        """Extract text content from the page and add metadata."""
        # Remove unwanted tags
        for tag in soup(['script', 'style', 'header', 'footer', 'nav']):
            tag.decompose()
        
        # Extract text content
        text = soup.get_text(separator=' ', strip=True)
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Extract title
        title = soup.title.string if soup.title else "No Title"
        
        # Create metadata
        metadata = {
            'source': url,
            'title': title,
            'information_types': self.identify_information_type(text + ' ' + title),
        }
        
        return text, metadata
    
    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch a webpage and return BeautifulSoup object."""
        try:
            response = requests.get(url, headers=self.get_headers(), timeout=self.timeout)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            print(f"Error fetching {url}: {e}")
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
    
    def scrape_all_universities(self) -> List[Document]:
        """Scrape all universities defined in the config."""
        all_documents = []
        for university in self.config['universities']:
            documents = self.scrape_university(university)
            all_documents.extend(documents)
        
        print(f"Total documents scraped: {len(all_documents)}")
        return all_documents

if __name__ == "__main__":
    scraper = WebScraper()
    documents = scraper.scrape_all_universities()
    print(f"Scraped {len(documents)} documents in total.") 