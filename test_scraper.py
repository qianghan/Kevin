#!/usr/bin/env python3
"""
Test script to debug the enhanced web scraper with RAG optimizations.
"""

import os
import sys
import time
import yaml
import json
import argparse
import pprint
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Check for required dependencies
def check_dependencies():
    missing_deps = []
    rust_tools_missing = False
    spider_package_name = None
    
    # Check for spider_rs package specifically
    try:
        import spider_rs
        spider_package_name = 'spider_rs'
    except ImportError:
        # Check for other possible spider packages as fallback
        for package_name in ['spiderpy', 'spider', 'spider_py']:
            try:
                if package_name == 'spiderpy':
                    import spiderpy
                    spider_package_name = 'spiderpy'
                    break
                elif package_name == 'spider':
                    import spider
                    spider_package_name = 'spider'
                    break
                elif package_name == 'spider_py':
                    import spider_py
                    spider_package_name = 'spider_py'
                    break
            except ImportError:
                continue
    except Exception as e:
        # Check if this is a Rust toolchain error
        if "Rust" in str(e) or "rust" in str(e) or "cargo" in str(e) or "Cargo" in str(e):
            missing_deps.append("spider_rs (Rust tools required)")
            rust_tools_missing = True
        else:
            missing_deps.append("spider_rs")
    
    if not spider_package_name and not rust_tools_missing:
        # No spider package was found
        missing_deps.append("spider_rs")
    
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        missing_deps.append("beautifulsoup4")
    
    try:
        from langchain.schema import Document
        from langchain.text_splitter import RecursiveCharacterTextSplitter
    except ImportError:
        missing_deps.append("langchain")
    
    if missing_deps:
        print("=" * 80)
        print("ERROR: Missing required dependencies")
        print("=" * 80)
        print("The following packages need to be installed:")
        for dep in missing_deps:
            print(f"  - {dep}")
        
        rust_instructions = ""
        if any("Rust" in dep for dep in missing_deps):
            rust_instructions = """
RUST INSTALLATION REQUIRED:
The spider_rs package requires Rust and Cargo to compile. You need to:

1. Install Rust toolchain first:
   - On macOS/Linux: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   - On Windows: Visit https://rustup.rs/ and download the installer

2. After installing Rust, run:
   pip install spider_rs

For more details, see https://www.rust-lang.org/tools/install
"""
        
        print("\nPlease install the missing packages using pip:")
        clean_deps = [dep.split(" ")[0] for dep in missing_deps if "Rust" not in dep]
        print(f"pip install {' '.join(clean_deps)}")
        
        if rust_instructions:
            print(rust_instructions)
        
        print("If you're using a virtual environment, make sure it's activated.")
        print("=" * 80)
        
        print("\nRunning in mock mode since spider_rs is not available or properly installed.")
        print("This mode will use synthetic data to test the RAG pipeline without scraping.")
        print("=" * 80)
        
        # Force mock data mode
        return True
    
    # Spider dependencies are installed
    return False

# Check dependencies and get result (True means need to use mock data)
use_mock_data = check_dependencies()

# Now import project modules (after dependency check)
try:
    # Try to import with a fallback
    try:
        from src.data.scraper import WebScraper, UniversityContentExtractor
    except ImportError as e:
        if "spider" in str(e).lower() or "rust" in str(e).lower() or "cargo" in str(e).lower():
            print("WARNING: Could not import WebScraper due to missing spider_rs package or Rust toolchain.")
            print("Using MockScraper instead for testing.")
            use_mock_data = True
            
    # Define a simple mock class for testing without the real scraper
    class MockDocument:
        def __init__(self, title, content, url, categories=None):
            self.page_content = content
            self.metadata = {
                'title': title,
                'source': url,
                'university': 'Mock University',
                'content_categories': categories or ['mock'],
                'word_count': len(content.split())
            }
    
    class MockScraper:
        def __init__(self):
            self.max_pages = 20
            self.enable_javascript = False
            self.spider_config = {'max_pages': 20, 'js_enabled': False}
            self.config = {
                'universities': [
                    {'name': 'Mock University', 'base_url': 'https://mock.edu'}
                ]
            }
        
        def scrape_university(self, university):
            print("MOCK MODE: Generating fake university data instead of scraping")
            docs = [
                MockDocument(
                    "Mock Admissions", 
                    "This is mock content about university admissions. Applications are accepted year-round. "
                    "Undergraduate applications are due by January 15 for the fall semester. "
                    "Graduate applications have rolling deadlines. International students should apply at least "
                    "6 months before their intended start date. Transfer students are welcome to apply.", 
                    "https://mock.edu/admissions",
                    ['admission']
                ),
                MockDocument(
                    "Mock Tuition and Financial Aid", 
                    "Tuition for the mock university is $10,000 per semester for domestic students and $15,000 "
                    "for international students. Financial aid is available through scholarships, grants, and loans. "
                    "Payment plans are available. The deadline for scholarship applications is March 1st each year.",
                    "https://mock.edu/tuition",
                    ['tuition', 'financial_aid']
                ),
                MockDocument(
                    "Mock Academic Programs", 
                    "We offer programs in Computer Science, Engineering, Business Administration, Arts, and Sciences. "
                    "Our most popular majors are Computer Science, Business, and Psychology. Graduate programs include "
                    "MBA, MS in Computer Science, and PhD in various disciplines. All programs are accredited.",
                    "https://mock.edu/programs",
                    ['programs', 'academics']
                ),
                MockDocument(
                    "Mock Student Life", 
                    "Campus housing includes dormitories and apartments. The student center features dining options, "
                    "study spaces, and recreational facilities. There are over 100 student clubs and organizations. "
                    "Athletics include intramural sports and varsity teams competing in Division III.",
                    "https://mock.edu/student-life",
                    ['student_life', 'housing']
                ),
                MockDocument(
                    "Mock Faculty Directory", 
                    "Our faculty includes world-renowned experts in their fields. The student-to-faculty ratio is 15:1. "
                    "Faculty office hours are typically held weekly. Research opportunities are available for students "
                    "to work directly with faculty members on cutting-edge projects.",
                    "https://mock.edu/faculty",
                    ['faculty', 'research']
                )
            ]
            return docs
        
    # Create a mock extractor
    class MockExtractor:
        def categorize_content(self, content, url):
            if "admission" in content.lower():
                return ["admission"]
            elif "tuition" in content.lower() or "financial aid" in content.lower():
                return ["tuition", "financial_aid"]
            elif "program" in content.lower() or "academic" in content.lower():
                return ["programs", "academics"]
            elif "student" in content.lower() or "campus" in content.lower():
                return ["student_life"]
            elif "faculty" in content.lower() or "professor" in content.lower():
                return ["faculty"]
            return ["general"]
    
    # Import document processor
    from src.core.document_processor import DocumentProcessor
    from langchain.schema import Document
    from langchain.text_splitter import RecursiveCharacterTextSplitter
except Exception as e:
    print(f"ERROR: Could not import project modules: {e}")
    print("Please check that the project structure is correct and all dependencies are installed.")
    sys.exit(1)

def format_time(seconds: float) -> str:
    """Format time in a human-readable way."""
    if seconds < 60:
        return f"{seconds:.2f} seconds"
    elif seconds < 3600:
        minutes = seconds // 60
        sec = seconds % 60
        return f"{int(minutes)} minutes {int(sec)} seconds"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        sec = seconds % 60
        return f"{int(hours)} hours {int(minutes)} minutes {int(sec)} seconds"

def test_scraping(max_pages: int = 20, university_name: Optional[str] = None, content_types: Optional[List[str]] = None, 
                  enable_js: bool = False, chunk_size: int = 500, chunk_overlap: int = 100,
                  clear_cache: bool = False, use_rag_mode: bool = True, use_mock_data: bool = False):
    """Run a test scrape and document processing with enhanced RAG capabilities."""
    print("=" * 80)
    print(f"TESTING ENHANCED WEB SCRAPER WITH RAG OPTIMIZATIONS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Initialize scraper
    print("\n[1] Initializing web scraper...")
    
    # Use mock scraper if needed
    if use_mock_data:
        print("  → Running in MOCK MODE (spider_rs not available or Rust toolchain missing)")
        scraper = MockScraper()
        extractor = MockExtractor()
    else:
        try:
            scraper = WebScraper()
            extractor = UniversityContentExtractor()
            # Check if this is still a real scraper (not automatically converted to mock)
            if not hasattr(scraper, 'spider_config'):
                print("  → Original scraper doesn't have expected attributes, switching to MOCK MODE")
                scraper = MockScraper()
                extractor = MockExtractor()
                use_mock_data = True
        except Exception as e:
            print(f"ERROR: Failed to initialize WebScraper: {e}")
            print("  → Switching to MOCK MODE due to initialization error")
            scraper = MockScraper()
            extractor = MockExtractor()
            use_mock_data = True
    
    # Set scraper options if not in mock mode
    if not use_mock_data:
        if max_pages:
            scraper.max_pages = max_pages
            scraper.spider_config['max_pages'] = max_pages
            print(f"  → Max pages set to: {max_pages}")
        
        if enable_js:
            scraper.enable_javascript = True
            scraper.spider_config['js_enabled'] = True
            print("  → JavaScript rendering enabled")
    else:
        print("  → Mock mode active - scraper options ignored")
    
    # Clear cache if requested and not in mock mode
    if clear_cache and not use_mock_data:
        cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache')
        if os.path.exists(cache_dir):
            print(f"  → Clearing cache directory: {cache_dir}")
            import shutil
            try:
                for item in os.listdir(cache_dir):
                    item_path = os.path.join(cache_dir, item)
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    else:
                        os.unlink(item_path)
                print("  → Cache cleared successfully")
            except Exception as e:
                print(f"  → Error clearing cache: {e}")
    
    # Get university to test
    university = None
    if not use_mock_data:
        if university_name:
            for uni in scraper.config['universities']:
                if uni['name'].lower() == university_name.lower():
                    university = uni
                    break
            
            if not university:
                print(f"ERROR: University '{university_name}' not found in configuration.")
                available_unis = [u['name'] for u in scraper.config['universities']]
                print(f"Available universities: {', '.join(available_unis)}")
                return []
        else:
            # Default to the first university in the config
            university = scraper.config['universities'][0]
    else:
        # In mock mode, create a mock university
        university = scraper.config['universities'][0]
        print(f"  → Using mock university: {university['name']}")
    
    print(f"\n[2] Testing scraping for: {university['name']}")
    if not use_mock_data:
        print(f"  → Base URL: {university['base_url']}")
        if 'focus_urls' in university:
            print(f"  → Focus URLs: {len(university['focus_urls'])}")
    else:
        print(f"  → MOCK MODE: Using pre-generated data")
    
    # Track timing
    scrape_start = time.time()
    
    # Scrape university
    try:
        documents = scraper.scrape_university(university)
        
        # If documents is empty and spider is not available, use mock data
        if len(documents) == 0:
            print("  → No documents were scraped, falling back to mock data")
            mock_scraper = MockScraper()
            documents = mock_scraper.scrape_university(university)
            use_mock_data = True
    except Exception as e:
        print(f"ERROR: Failed to scrape university: {e}")
        print("  → Using mock documents instead due to error")
        mock_scraper = MockScraper()
        documents = mock_scraper.scrape_university(university)
        use_mock_data = True
    
    scrape_end = time.time()
    scrape_time = scrape_end - scrape_start
    
    print(f"\n[3] Scraping completed in {format_time(scrape_time)}")
    print(f"  → {'Generated' if use_mock_data else 'Scraped'} {len(documents)} documents from {university['name']}")
    if not use_mock_data:
        print(f"  → Average time per page: {scrape_time / max(len(documents), 1):.2f} seconds")
    
    if len(documents) == 0:
        print("ERROR: No documents were scraped! Check the scraper configuration and network connectivity.")
        return []
    
    # Filter by content type if specified
    if content_types:
        print(f"\n[4] Filtering documents by content types: {', '.join(content_types)}")
        filtered_documents = []
        for doc in documents:
            # Check content categories in metadata
            categories = doc.metadata.get('content_categories', [])
            if not categories:
                # Check information types as fallback
                info_types = doc.metadata.get('information_types', '')
                if info_types:
                    categories = info_types.split(',')
            
            # Keep document if it matches any requested content type
            if any(ct in (cat.lower() if isinstance(cat, str) else cat) for cat in categories for ct in content_types):
                filtered_documents.append(doc)
            # Also keep documents without category if they contain relevant keywords in the title
            elif any(ct in doc.metadata.get('title', '').lower() for ct in content_types):
                filtered_documents.append(doc)
        
        print(f"  → Filtered from {len(documents)} to {len(filtered_documents)} documents based on content types")
        documents = filtered_documents
    
    # Print document samples
    print("\n[5] Document Samples (first 3):")
    for i, doc in enumerate(documents[:3]):
        print(f"\nDocument {i+1}/{min(3, len(documents))}:")
        print(f"  → Title: {doc.metadata.get('title', 'No Title')}")
        print(f"  → URL: {doc.metadata.get('source', 'No URL')}")
        print(f"  → Information Types: {doc.metadata.get('information_types', 'None')}")
        print(f"  → Content Categories: {doc.metadata.get('content_categories', 'None')}")
        print(f"  → Word Count: {doc.metadata.get('word_count', 0)}")
        print(f"  → Content Sample (first 100 chars): {doc.page_content[:100]}...")
        
        # Print structured data if available
        if 'structured_data' in doc.metadata:
            print("  → Contains structured data:")
            if 'emails' in doc.metadata['structured_data']:
                print(f"     * Emails: {doc.metadata['structured_data']['emails']}")
            if 'phones' in doc.metadata['structured_data']:
                print(f"     * Phones: {doc.metadata['structured_data']['phones']}")
    
    # Test RAG processing if enabled
    if use_rag_mode:
        print("\n[6] Processing documents for RAG optimization...")
        rag_start = time.time()
        
        # Create sections from document content when available
        processed_documents = []
        
        for doc in documents:
            # Check if we have sections in metadata
            if 'sections' in doc.metadata:
                # Create a new document for each section
                metadata = doc.metadata.copy()
                university_name = metadata.get('university', 'Unknown University')
                
                for section_name in doc.metadata['sections']:
                    if section_name == 'main':
                        continue  # Skip general main section
                    
                    # Create a section-specific document
                    section_content = section_name + ": " + doc.page_content
                    section_metadata = metadata.copy()
                    section_metadata['section'] = section_name
                    section_metadata['is_section'] = True
                    section_metadata['source_with_section'] = f"{metadata.get('source', '')}#{section_name}"
                    
                    # Find content categories if not already set
                    if 'content_categories' not in section_metadata:
                        try:
                            categories = extractor.categorize_content(section_content, doc.metadata.get('source', ''))
                            if categories:
                                section_metadata['content_categories'] = categories
                        except Exception as e:
                            print(f"Error categorizing content: {e}")
                            
                    processed_documents.append({
                        'content': section_content,
                        'metadata': section_metadata
                    })
            else:
                # Process the whole document if no sections
                processed_documents.append({
                    'content': doc.page_content,
                    'metadata': doc.metadata
                })
        
        print(f"  → Created {len(processed_documents)} processing units from {len(documents)} documents")
        
        # Use optimal chunking for RAG
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", ", ", " ", ""]
        )
        
        # Split documents into chunks
        chunked_documents = []
        
        for doc_dict in processed_documents:
            chunks = text_splitter.create_documents(
                texts=[doc_dict['content']],
                metadatas=[doc_dict['metadata']]
            )
            chunked_documents.extend(chunks)
        
        print(f"  → Created {len(chunked_documents)} chunks using size={chunk_size}, overlap={chunk_overlap}")
        
        rag_end = time.time()
        rag_time = rag_end - rag_start
        print(f"  → RAG processing completed in {format_time(rag_time)}")
        
        # Test adding to vector store
        print("\n[7] Testing Document Processor (Vector Storage)...")
        try:
            processor = DocumentProcessor()
        except Exception as e:
            print(f"ERROR: Failed to initialize DocumentProcessor: {e}")
            print("Check your configuration files and make sure all dependencies are installed.")
            return documents
        
        # Clear existing database or create backup
        if os.path.exists(processor.persist_directory):
            print("  → Creating backup of existing vector store...")
            import shutil
            try:
                # Create a backup
                backup_dir = f"{processor.persist_directory}_backup_{int(time.time())}"
                shutil.copytree(processor.persist_directory, backup_dir)
                print(f"  → Backed up existing database to {backup_dir}")
            except Exception as e:
                print(f"  → Could not backup database: {e}")
        
        # Add documents to vector store
        vectorize_start = time.time()
        print(f"  → Adding {len(chunked_documents)} chunks to vector store...")
        try:
            processor.add_documents(chunked_documents)
        except Exception as e:
            print(f"ERROR: Failed to add documents to vector store: {e}")
            print("Check your vector store configuration and make sure all dependencies are installed.")
            return documents
            
        vectorize_end = time.time()
        vectorize_time = vectorize_end - vectorize_start
        
        print(f"  → Vectorization completed in {format_time(vectorize_time)}")
        
        # Generate a summary report
        summary = {
            'timestamp': datetime.now().isoformat(),
            'university': university['name'],
            'mock_mode': use_mock_data,
            'total_documents': len(documents),
            'total_processing_units': len(processed_documents),
            'total_chunks': len(chunked_documents),
            'content_types': content_types if content_types else 'all',
            'chunk_size': chunk_size,
            'chunk_overlap': chunk_overlap,
            'timing': {
                'scraping_seconds': scrape_time,
                'rag_processing_seconds': rag_time,
                'vectorization_seconds': vectorize_time,
                'total_seconds': scrape_time + rag_time + vectorize_time
            }
        }
        
        # Print timing summary
        print("\n[8] Processing Summary:")
        print(f"  → {'Mock Data Generation' if use_mock_data else 'Scraping'}: {format_time(scrape_time)}")
        print(f"  → RAG Processing: {format_time(rag_time)}")
        print(f"  → Vectorization: {format_time(vectorize_time)}")
        print(f"  → Total Processing Time: {format_time(scrape_time + rag_time + vectorize_time)}")
        
        # Write summary to a file
        summary_path = os.path.join(os.path.dirname(processor.persist_directory), 'test_summary.json')
        try:
            with open(summary_path, 'w') as f:
                json.dump(summary, f, indent=2)
            print(f"  → Summary written to {summary_path}")
        except Exception as e:
            print(f"  → Could not write summary: {e}")
        
        # Test searching
        print("\n[9] Testing Search...")
        search_start = time.time()
        query = f"Tell me about {university['name']}"
        print(f"  → Searching for: '{query}'")
        try:
            results = processor.search_documents(query, k=3)
            search_end = time.time()
            
            print(f"  → Found {len(results)} results in {(search_end - search_start):.2f} seconds")
            if results:
                print("\n  First result (first 100 chars):")
                print(f"  → {results[0].page_content[:100]}...")
                print(f"  → Source: {results[0].metadata.get('source', 'Unknown')}")
                if 'section' in results[0].metadata:
                    print(f"  → Section: {results[0].metadata['section']}")
        except Exception as e:
            print(f"ERROR: Search failed: {e}")
    
    return documents

def main():
    """Parse arguments and run test."""
    parser = argparse.ArgumentParser(description="Test the enhanced web scraper with RAG capabilities")
    parser.add_argument("--university", type=str, help="Name of university to scrape")
    parser.add_argument("--max-pages", type=int, default=20, help="Maximum number of pages to scrape")
    parser.add_argument("--content-types", type=str, help="Comma-separated types of content to target (admission,tuition,programs,faculty,etc)")
    parser.add_argument("--enable-js", action="store_true", help="Enable JavaScript for web scraping")
    parser.add_argument("--chunk-size", type=int, default=500, help="Chunk size for document splitting")
    parser.add_argument("--chunk-overlap", type=int, default=100, help="Chunk overlap for document splitting")
    parser.add_argument("--clear-cache", action="store_true", help="Clear scraping cache before starting")
    parser.add_argument("--no-rag", action="store_true", help="Skip RAG optimization processing")
    parser.add_argument("--mock-data", action="store_true", help="Use mock data instead of real scraping")
    
    args = parser.parse_args()
    
    # Parse content types if provided
    content_types = None
    if args.content_types:
        content_types = args.content_types.split(",")
    
    # Force mock data mode if detected by dependency check
    # Get the value from global scope
    global use_mock_data
    force_mock = args.mock_data or use_mock_data
    if force_mock and not args.mock_data:
        print("NOTE: Forcing mock data mode due to missing dependencies")
    
    start_time = time.time()
    test_scraping(
        max_pages=args.max_pages,
        university_name=args.university,
        content_types=content_types,
        enable_js=args.enable_js,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        clear_cache=args.clear_cache,
        use_rag_mode=not args.no_rag,
        use_mock_data=force_mock
    )
    elapsed_time = time.time() - start_time
    
    print("\n" + "=" * 80)
    print(f"Test completed in {format_time(elapsed_time)}")
    print("=" * 80)

if __name__ == "__main__":
    main() 