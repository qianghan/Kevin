#!/usr/bin/env python3
"""
Integration Test for Canadian University Information Agent
This script tests all major components of the system:
1. Web scraping (scrape mode)
2. Vector database updating (train mode)
3. RAG knowledge base creation (rag mode)
4. Query functionality (query mode)

Usage:
    python test_integration.py [--verbose] [--university UNIVERSITY]
"""

import os
import sys
import time
import json
import logging
import argparse
import subprocess
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

def test_scrape_mode(university: Optional[str] = None, max_pages: int = 5) -> bool:
    """Test the scrape mode with limited scope."""
    logger.info("🔍 TESTING SCRAPE MODE")
    
    # Build command
    command = ["python", "src/main.py", "--mode", "scrape", "--max-pages", str(max_pages)]
    
    # Add university if specified
    if university:
        command.extend(["--university", university])
    
    # Run command
    exit_code, stdout, stderr = run_command(command)
    
    # Check results
    if exit_code != 0:
        logger.error(f"Scrape mode failed with exit code {exit_code}")
        logger.error(f"stderr: {stderr}")
        return False
    
    # Check for backup files
    backup_dir = Path("data/backup")
    if not backup_dir.exists() or not any(backup_dir.glob("scrape_backup_*.json")):
        logger.error("No backup files found after scraping")
        return False
    
    logger.info("✅ Scrape mode test passed")
    return True

def test_train_mode() -> bool:
    """Test the train mode."""
    logger.info("🧠 TESTING TRAIN MODE")
    
    # Build command
    command = ["python", "src/main.py", "--mode", "train"]
    
    # Run command
    exit_code, stdout, stderr = run_command(command)
    
    # Check results
    if exit_code != 0:
        logger.error(f"Train mode failed with exit code {exit_code}")
        logger.error(f"stderr: {stderr}")
        return False
    
    # Check for vector database
    vector_dir = Path("data/vectordb")
    if not vector_dir.exists():
        logger.error("Vector database directory not found after training")
        return False
    
    logger.info("✅ Train mode test passed")
    return True

def test_rag_mode(university: Optional[str] = None, max_pages: int = 5) -> bool:
    """Test the RAG mode with limited scope."""
    logger.info("📚 TESTING RAG MODE")
    
    # Build command
    command = ["python", "src/main.py", "--mode", "rag", "--max-pages", str(max_pages)]
    
    # Add university if specified
    if university:
        command.extend(["--university", university])
    
    # Run command
    exit_code, stdout, stderr = run_command(command)
    
    # Check results
    if exit_code != 0:
        logger.error(f"RAG mode failed with exit code {exit_code}")
        logger.error(f"stderr: {stderr}")
        return False
    
    # Check for vector database and summary
    vector_dir = Path("data/vectordb")
    summary_file = vector_dir / "index_summary.json"
    
    if not vector_dir.exists():
        logger.error("Vector database directory not found after RAG mode")
        return False
    
    if not summary_file.exists():
        logger.error("Index summary file not found after RAG mode")
        return False
    
    logger.info("✅ RAG mode test passed")
    return True

def test_query_mode(queries: List[Dict[str, Any]]) -> bool:
    """Test the query mode with a set of test queries."""
    logger.info("❓ TESTING QUERY MODE")
    
    all_passed = True
    results = []
    
    for idx, query_info in enumerate(queries):
        query = query_info["query"]
        expected_keywords = query_info["expected_keywords"]
        
        logger.info(f"Testing query {idx+1}/{len(queries)}: {query}")
        
        # Build command
        command = ["python", "src/main.py", "--mode", "query", "--query", query]
        
        # Run command
        exit_code, stdout, stderr = run_command(command)
        
        # Check results
        if exit_code != 0:
            logger.error(f"Query mode failed with exit code {exit_code}")
            logger.error(f"stderr: {stderr}")
            all_passed = False
            results.append({
                "query": query,
                "success": False,
                "error": stderr,
                "keywords_found": []
            })
            continue
        
        # Check for expected keywords in output
        keywords_found = [kw for kw in expected_keywords if kw.lower() in stdout.lower()]
        
        if len(keywords_found) / len(expected_keywords) < 0.5:  # At least 50% of keywords should be found
            logger.warning(f"Query didn't return expected content. Found {len(keywords_found)}/{len(expected_keywords)} keywords")
            all_passed = False
            results.append({
                "query": query,
                "success": False,
                "keywords_found": keywords_found,
                "keywords_missing": [kw for kw in expected_keywords if kw not in keywords_found]
            })
        else:
            logger.info(f"Query returned expected content. Found {len(keywords_found)}/{len(expected_keywords)} keywords")
            results.append({
                "query": query,
                "success": True,
                "keywords_found": keywords_found
            })
    
    # Save detailed results
    results_dir = Path("test_results")
    results_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = results_dir / f"query_test_results_{timestamp}.json"
    
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Detailed query test results saved to {results_file}")
    
    if all_passed:
        logger.info("✅ Query mode test passed")
    else:
        logger.warning("⚠️ Query mode test partially passed")
    
    return all_passed

def main():
    """Run the integration test."""
    parser = argparse.ArgumentParser(description="Integration Test for Canadian University Information Agent")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--university", type=str, help="Specify a single university to test")
    parser.add_argument("--max-pages", type=int, default=5, help="Maximum pages to scrape per university")
    parser.add_argument("--skip-scrape", action="store_true", help="Skip the scrape test")
    parser.add_argument("--skip-train", action="store_true", help="Skip the train test")
    parser.add_argument("--skip-rag", action="store_true", help="Skip the RAG test")
    parser.add_argument("--skip-query", action="store_true", help="Skip the query test")
    
    args = parser.parse_args()
    
    # Update logging level
    global logger
    logger = setup_logging(args.verbose)
    
    # Save start time
    start_time = time.time()
    
    # Print banner
    logger.info("=" * 80)
    logger.info("CANADIAN UNIVERSITY INFORMATION AGENT - INTEGRATION TEST")
    logger.info("=" * 80)
    
    # Run tests
    test_results = {
        "scrape": None,
        "train": None,
        "rag": None,
        "query": None
    }
    
    try:
        # Test scrape mode
        if not args.skip_scrape:
            test_results["scrape"] = test_scrape_mode(args.university, args.max_pages)
        else:
            logger.info("Skipping scrape test")
        
        # Test train mode
        if not args.skip_train:
            test_results["train"] = test_train_mode()
        else:
            logger.info("Skipping train test")
        
        # Test RAG mode
        if not args.skip_rag:
            test_results["rag"] = test_rag_mode(args.university, args.max_pages)
        else:
            logger.info("Skipping RAG test")
        
        # Test query mode
        if not args.skip_query:
            test_results["query"] = test_query_mode(TEST_QUERIES)
        else:
            logger.info("Skipping query test")
    
    except Exception as e:
        logger.error(f"Test failed with unhandled exception: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    # Calculate elapsed time
    elapsed_time = time.time() - start_time
    
    # Print summary
    logger.info("=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total time: {elapsed_time:.2f} seconds")
    
    for test_name, result in test_results.items():
        if result is None:
            status = "SKIPPED"
        elif result:
            status = "PASSED"
        else:
            status = "FAILED"
        
        logger.info(f"{test_name.upper(): <10} : {status}")
    
    # Determine overall success
    executed_tests = [result for result in test_results.values() if result is not None]
    if executed_tests and all(executed_tests):
        logger.info("=" * 80)
        logger.info("🎉 ALL TESTS PASSED! 🎉")
        logger.info("=" * 80)
        sys.exit(0)
    elif not executed_tests:
        logger.warning("=" * 80)
        logger.warning("⚠️ NO TESTS WERE EXECUTED ⚠️")
        logger.warning("=" * 80)
        sys.exit(1)
    else:
        logger.error("=" * 80)
        logger.error("❌ SOME TESTS FAILED ❌")
        logger.error("=" * 80)
        sys.exit(1)

if __name__ == "__main__":
    main() 