#!/usr/bin/env python3
"""
Main entry point for the Canadian University Information Agent.
This script provides a convenient way to run different components of the system.
"""

import os
import sys
import argparse
from dotenv import load_dotenv

# Add src to path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

def main():
    """Parse arguments and run the appropriate component."""
    parser = argparse.ArgumentParser(
        description="Canadian University Information Agent"
    )
    parser.add_argument(
        "--mode", 
        choices=["web", "scrape", "query", "train"], 
        default="web",
        help="Mode to run (web=Streamlit interface, scrape=Run web scraper, query=Direct query, train=Update vector DB)"
    )
    parser.add_argument(
        "--query", 
        type=str,
        help="Query to process (required for query mode)"
    )
    parser.add_argument(
        "--web-search", 
        action="store_true",
        help="Enable web search for up-to-date information"
    )
    
    args = parser.parse_args()
    
    if args.mode == "web":
        # Run Streamlit web interface using our launcher script
        print("Starting web interface...")
        # Set environment variables to ensure DeepSeek API is used
        os.environ['USE_DEEPSEEK_ONLY'] = '1'
        os.environ['TORCH_WARN_ONCE'] = '1'
        
        # Use the launcher script
        launcher_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "run_kevin.py")
        if os.path.exists(launcher_path):
            os.system(f"python {launcher_path}")
        else:
            # Fallback to direct streamlit run with environment variables set
            os.system("streamlit run src/web/app.py")
    
    elif args.mode == "scrape":
        # Run web scraper
        print("Running web scraper...")
        from src.data.scraper import WebScraper
        from src.core.document_processor import DocumentProcessor
        
        scraper = WebScraper()
        documents = scraper.scrape_all_universities()
        
        print(f"Scraped {len(documents)} documents")
        processor = DocumentProcessor()
        processor.add_documents(documents)
        print("Documents added to vector store")
    
    elif args.mode == "query":
        # Process a direct query
        if not args.query:
            print("Error: --query argument is required for query mode")
            sys.exit(1)
        
        print(f"Processing query: {args.query}")
        from src.core.agent import UniversityAgent
        
        agent = UniversityAgent()
        response = agent.query(args.query, use_web_search=args.web_search)
        
        print("\nResponse:")
        print("-" * 80)
        print(response)
        print("-" * 80)
    
    elif args.mode == "train":
        # Update vector database
        print("Updating vector database...")
        from src.data.scraper import WebScraper
        from src.core.document_processor import DocumentProcessor
        
        scraper = WebScraper()
        documents = scraper.scrape_all_universities()
        
        print(f"Scraped {len(documents)} documents")
        processor = DocumentProcessor()
        processor.add_documents(documents)
        print("Vector database updated successfully")

if __name__ == "__main__":
    main() 