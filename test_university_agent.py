#!/usr/bin/env python3
"""
Unit Tests for Canadian University Information Agent
This script provides a pytest-compatible suite of tests for all major components.

Usage:
    python -m pytest test_university_agent.py -v
    
    # Run specific test class
    python -m pytest test_university_agent.py::TestScraper -v
    
    # Run with more detailed logging
    python -m pytest test_university_agent.py -v --log-cli-level=INFO
"""

import os
import sys
import time
import json
import logging
import subprocess
import unittest
import pytest
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Configure logging
def setup_logging(verbose=False):
    """Set up logging configuration."""
    # Configure the root logger - this is the most direct approach
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)  # Explicitly use stdout
        ]
    )
    
    # Verify logging is working with a test message
    logger = logging.getLogger()
    logger.info("====== CONSOLE LOGGING INITIALIZED ======")
    logger.info("(If you see this message, logging to console is working)")
    
    return logger

# Initialize logger with default configuration
logger = setup_logging()

# Test queries with expected content keywords
TEST_QUERIES = [
    {
        "query": "What are the admission requirements for undergraduate programs?",
        "expected_keywords": ["admission", "requirements", "undergraduate", "application"]
    },
    {
        "query": "Tell me about tuition fees for international students",
        "expected_keywords": ["tuition", "fees", "international", "students", "cost"]
    },
    {
        "query": "What programs are offered in computer science?",
        "expected_keywords": ["program", "computer science", "degree", "courses"]
    },
    {
        "query": "What are the application deadlines?",
        "expected_keywords": ["deadline", "application", "date", "submit"]
    }
]

def run_command(command: List[str], timeout: int = 1800) -> (int, str, str):
    """Run a command and return exit code, stdout, and stderr."""
    logger.info(f"Running command: {' '.join(command)}")
    
    try:
        # Run process without capturing output to allow real-time console display
        process = subprocess.Popen(
            command,
            # Let output go directly to the console
            stdout=None,
            stderr=None,
            text=True
        )
        
        # Wait for completion
        process.wait(timeout=timeout)
        
        logger.info(f"Command completed with exit code: {process.returncode}")
        return process.returncode, "", ""  # Empty strings since we're not capturing
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out after {timeout} seconds")
        return 1, "", f"Command timed out after {timeout} seconds"
    except Exception as e:
        logger.error(f"Error running command: {e}")
        return 1, "", str(e)


class TestScraper(unittest.TestCase):
    """Test cases for the web scraper component."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class."""
        # Ensure data directory exists
        os.makedirs("data/backup", exist_ok=True)
        
        # Set up small test with just one university and limited pages
        cls.university = None  # Set to a specific university name to test only that one
        cls.max_pages = 3
    
    def test_01_scrape_mode(self):
        """Test the scrape mode with limited scope."""
        logger.info("🔍 TESTING SCRAPE MODE")
        
        # Build command
        command = ["python", "src/main.py", "--mode", "scrape", "--max-pages", str(self.max_pages)]
        
        # Add university if specified
        if self.university:
            command.extend(["--university", self.university])
        
        # Run command
        exit_code, stdout, stderr = run_command(command)
        
        # Check results
        self.assertEqual(exit_code, 0, f"Scrape mode failed with exit code {exit_code}. Error: {stderr}")
        
        # Check for backup files
        backup_dir = Path("data/backup")
        self.assertTrue(backup_dir.exists(), "Backup directory doesn't exist")
        
        # Check if any backup files were created
        backup_files = list(backup_dir.glob("scrape_backup_*.json"))
        self.assertTrue(len(backup_files) > 0, "No backup files found after scraping")
        
        # Check content of the latest backup file
        latest_backup = sorted(backup_files)[-1]
        with open(latest_backup, 'r') as f:
            backup_data = json.load(f)
        
        self.assertTrue(len(backup_data) > 0, f"Backup file {latest_backup} contains no documents")
        
        # Check structure of backup data
        self.assertIn("page_content", backup_data[0], "Backup data missing page_content field")
        self.assertIn("metadata", backup_data[0], "Backup data missing metadata field")
        
        logger.info(f"✅ Found {len(backup_data)} documents in backup file {latest_backup}")


class TestTrainingMode(unittest.TestCase):
    """Test cases for the training mode."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class."""
        # Ensure vector database directory exists
        os.makedirs("data/vectordb", exist_ok=True)
    
    def test_01_train_mode(self):
        """Test the train mode."""
        logger.info("🧠 TESTING TRAIN MODE")
        
        # Build command
        command = ["python", "src/main.py", "--mode", "train"]
        
        # Run command
        exit_code, stdout, stderr = run_command(command)
        
        # Check results
        self.assertEqual(exit_code, 0, f"Train mode failed with exit code {exit_code}. Error: {stderr}")
        
        # Check for vector database
        vector_dir = Path("data/vectordb")
        self.assertTrue(vector_dir.exists(), "Vector database directory not found after training")
        
        # Check if any files were created in the vector database directory
        vector_files = list(vector_dir.glob("*.bin"))
        self.assertTrue(len(vector_files) > 0 or 
                        vector_dir.joinpath("index").exists() or
                        vector_dir.joinpath("chroma").exists(), 
                        "No vector database files found after training")
        
        logger.info("✅ Vector database successfully created/updated")


class TestRAGMode(unittest.TestCase):
    """Test cases for the RAG mode."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class."""
        # Set up small test with just one university and limited pages
        cls.university = None  # Set to a specific university name to test only that one
        cls.max_pages = 3
    
    def test_01_rag_mode(self):
        """Test the RAG mode with limited scope."""
        logger.info("📚 TESTING RAG MODE")
        
        # Build command
        command = ["python", "src/main.py", "--mode", "rag", "--max-pages", str(self.max_pages)]
        
        # Add university if specified
        if self.university:
            command.extend(["--university", self.university])
        
        # Run command
        exit_code, stdout, stderr = run_command(command)
        
        # Check results
        self.assertEqual(exit_code, 0, f"RAG mode failed with exit code {exit_code}. Error: {stderr}")
        
        # Check for vector database and summary
        vector_dir = Path("data/vectordb")
        summary_file = vector_dir / "index_summary.json"
        
        self.assertTrue(vector_dir.exists(), "Vector database directory not found after RAG mode")
        self.assertTrue(summary_file.exists(), "Index summary file not found after RAG mode")
        
        # Check content of summary file
        with open(summary_file, 'r') as f:
            summary_data = json.load(f)
        
        self.assertIn("total_chunks", summary_data, "Summary missing total_chunks field")
        self.assertIn("successful_chunks", summary_data, "Summary missing successful_chunks field")
        
        logger.info(f"✅ RAG mode processed {summary_data.get('total_chunks', 0)} chunks with {summary_data.get('successful_chunks', 0)} successes")


class TestQueryMode(unittest.TestCase):
    """Test cases for the query mode."""
    
    def test_01_query_mode(self):
        """Test the query mode with a set of test queries."""
        logger.info("❓ TESTING QUERY MODE")
        
        results = []
        
        for idx, query_info in enumerate(TEST_QUERIES):
            query = query_info["query"]
            expected_keywords = query_info["expected_keywords"]
            
            logger.info(f"Testing query {idx+1}/{len(TEST_QUERIES)}: {query}")
            
            # Build command
            command = ["python", "src/main.py", "--mode", "query", "--query", query]
            
            # Run command
            exit_code, stdout, stderr = run_command(command)
            
            # Check results
            self.assertEqual(exit_code, 0, f"Query mode failed with exit code {exit_code}. Error: {stderr}")
            
            # Check for expected keywords in output
            keywords_found = [kw for kw in expected_keywords if kw.lower() in stdout.lower()]
            
            # Log found keywords
            logger.info(f"Found {len(keywords_found)}/{len(expected_keywords)} expected keywords")
            
            # We expect at least some of the keywords to be found, but not necessarily all
            # This is a softer assertion as content might vary
            self.assertTrue(len(keywords_found) > 0, f"No expected keywords found in query results for: {query}")
            
            # Store results for reporting
            results.append({
                "query": query,
                "keywords_found": keywords_found,
                "keywords_missing": [kw for kw in expected_keywords if kw not in keywords_found],
                "success": len(keywords_found) > 0
            })
        
        # Save detailed results
        results_dir = Path("test_results")
        results_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = results_dir / f"query_test_results_{timestamp}.json"
        
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Detailed query test results saved to {results_file}")
        logger.info("✅ Query mode tests completed")


class TestEndToEnd(unittest.TestCase):
    """End-to-end test running all components in sequence."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class."""
        # Set up small test with just one university and limited pages
        cls.university = None  # Set to a specific university name to test only that one
        cls.max_pages = 3
        
        # Ensure directories exist
        os.makedirs("data/backup", exist_ok=True)
        os.makedirs("data/vectordb", exist_ok=True)
        os.makedirs("test_results", exist_ok=True)
        
        # Set start time
        cls.start_time = time.time()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after tests."""
        elapsed_time = time.time() - cls.start_time
        logger.info(f"Total test time: {elapsed_time:.2f} seconds")
    
    def test_01_scrape(self):
        """Run scrape mode as part of end-to-end test."""
        TestScraper.university = self.university
        TestScraper.max_pages = self.max_pages
        scraper_test = TestScraper("test_01_scrape_mode")
        scraper_test.test_01_scrape_mode()
    
    def test_02_train(self):
        """Run train mode as part of end-to-end test."""
        train_test = TestTrainingMode("test_01_train_mode")
        train_test.test_01_train_mode()
    
    def test_03_rag(self):
        """Run RAG mode as part of end-to-end test."""
        TestRAGMode.university = self.university
        TestRAGMode.max_pages = self.max_pages
        rag_test = TestRAGMode("test_01_rag_mode")
        rag_test.test_01_rag_mode()
    
    def test_04_query(self):
        """Run query mode as part of end-to-end test."""
        query_test = TestQueryMode("test_01_query_mode")
        query_test.test_01_query_mode()


if __name__ == "__main__":
    unittest.main() 