#!/usr/bin/env python3
"""
Main entry point for the Canadian University Information Agent.
This script provides a convenient way to run different components of the system.
"""

import os
import sys
import argparse
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
import traceback
import json
import logging
from langchain_core.documents import Document

# Configure logging
def setup_logging(log_level=None):
    """Set up logging with the specified level."""
    # Allow overriding from environment variable
    env_log_level = os.environ.get("LOG_LEVEL")
    if env_log_level and not log_level:
        log_level = env_log_level.upper()
    
    # Default to INFO if no level is specified
    if not log_level:
        log_level = "INFO"
    
    # Convert string to logging level
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        print(f"Invalid log level: {log_level}, defaulting to INFO")
        numeric_level = logging.INFO
    
    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Configure library loggers to be less verbose
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("filelock").setLevel(logging.WARNING)
    logging.getLogger("transformers").setLevel(logging.WARNING)
    
    # Return the logger for the current module
    return logging.getLogger(__name__)

# Initialize logger with default configuration
logger = setup_logging()

# Add src to path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

def get_parser():
    """
    Set up the argument parser.
    """
    parser = argparse.ArgumentParser(description='University Assistant')
    parser.add_argument('--config', default='config.yaml', help='Path to config file')
    parser.add_argument('--model', help='Model to use for embeddings')
    parser.add_argument('--university', help='University name to focus on')
    parser.add_argument('--max-pages', type=int, help='Maximum pages to scrape per university')
    parser.add_argument('--cache', action='store_true', help='Use cached data if available')
    parser.add_argument('--verbose', '-v', action='count', default=0, help='Increase verbosity')
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress INFO logs, show only warnings and errors')

    # Add mode argument
    parser.add_argument('mode', choices=['scrape', 'train', 'rag'], 
                        help='Mode of operation: scrape data, train model, or run RAG system')

    return parser

def main():
    """
    Main entry point for the application.
    """
    global logger  # Use the global logger variable
    parser = get_parser()
    args = parser.parse_args()
    
    # Set up logging based on verbosity level
    if args.quiet:
        log_level = "WARNING"  # Only show warnings and errors
    elif args.verbose == 0:
        log_level = "INFO"
    elif args.verbose == 1:
        log_level = "DEBUG"
    else:
        log_level = "DEBUG"
    
    # Update the global logger with the new log level
    logger = setup_logging(log_level)
    
    logger.info(f"Starting in {args.mode} mode")
    
    # Load configuration
    if os.path.isabs(args.config):
        config_path = args.config
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        config_path = os.path.join(project_root, args.config)
    
    # Check if the config file exists
    if not os.path.exists(config_path):
        logger.error(f"Config file not found: {config_path}")
        sys.exit(1)
    
    logger.info(f"Using config file: {config_path}")
    
    if args.mode == 'scrape':
        logger.info("🕸️ Starting web scraping...")
        
        # Import scraper module
        from data.scraper import WebScraper
        
        # Initialize the scraper
        scraper = WebScraper(config_path, max_pages=args.max_pages, quiet=args.quiet)
        
        # Scrape a single university or all universities
        if args.university:
            # Find the university in the configuration
            universities = scraper.config.get('universities', [])
            university = next((u for u in universities if u.get('name') == args.university), None)
            
            if university:
                logger.info(f"Scraping single university: {args.university}")
                documents = scraper.scrape_university(university)
                logger.info(f"Scraped {len(documents)} documents from {args.university}")
            else:
                logger.error(f"University '{args.university}' not found in config")
                sys.exit(1)
        else:
            logger.info("Scraping all universities in config")
            documents = scraper.scrape_all_universities()
            logger.info(f"Scraped {len(documents)} documents from all universities")
        
        logger.info("Web scraping completed!")
        
    elif args.mode == 'train':
        logger.info("🧠 Starting model training...")
        
        try:
            # Import trainer module
            from models.trainer import EmbeddingTrainer
            
            # Initialize the trainer
            trainer = EmbeddingTrainer(config_path)
            
            # Train the model
            trainer.train()
            
            logger.info("Model training completed!")
            
        except Exception as e:
            logger.error(f"Error during training: {e}")
            logger.error(traceback.format_exc())
            sys.exit(1)
        
    elif args.mode == 'rag':
        logger.info("🤖 Starting RAG system...")
        
        try:
            # Import RAG module
            from rag.engine import RAGEngine
            
            # Initialize the RAG engine
            engine = RAGEngine(config_path)
            
            # Start interactive session
            engine.interactive_session()
            
        except Exception as e:
            logger.error(f"Error during RAG session: {e}")
            logger.error(traceback.format_exc())
            sys.exit(1)
        
    else:
        logger.error(f"Unknown mode: {args.mode}")
        sys.exit(1)

if __name__ == "__main__":
    main() 