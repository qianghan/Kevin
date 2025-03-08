"""
Mock classes for testing and fallback when the real implementations can't be initialized.
"""

import time
import logging
from typing import List, Dict, Any

# Configure module logger
logger = logging.getLogger(__name__)

class MockAgent:
    """
    Mock agent for testing or when dependencies are missing.
    Provides a simplified interface compatible with the real agent.
    """
    def __init__(self):
        """Initialize the mock agent"""
        logger.info("Initializing mock agent")
        self.model_name = "mock-model"
        
    def query(self, query_text: str, use_web_search: bool = False) -> Dict[str, Any]:
        """
        Return a mock response that mimics the real agent's output format.
        
        Args:
            query_text: The query to process
            use_web_search: Whether to simulate web search
            
        Returns:
            Dict with output and thinking steps
        """
        logger.info(f"Mock agent received query: {query_text}")
        
        # Create a timestamp for the response
        timestamp = time.strftime("%H:%M:%S")
        
        # Create some mock thinking steps
        thinking_steps = [
            {
                "type": "query_analysis",
                "description": "Analyzing query",
                "duration_ms": 150,
                "content": f"Received query: {query_text}",
                "time": timestamp
            }
        ]
        
        # Add web search step if requested
        if use_web_search:
            thinking_steps.append({
                "type": "web_search",
                "description": "Simulating web search",
                "duration_ms": 500,
                "content": "No real search performed in mock mode",
                "time": timestamp
            })
        
        # Add response generation step
        thinking_steps.append({
            "type": "response_generation",
            "description": "Generating response",
            "duration_ms": 300,
            "content": "Creating mock response",
            "time": timestamp
        })
        
        return {
            "output": f"This is a mock response to your query: '{query_text}'\n\nThe real agent couldn't be initialized, so I'm providing this placeholder response instead.",
            "thinking": thinking_steps
        }
    
    def get_documents(self, query: str) -> List[Any]:
        """
        Return empty document list for the mock agent.
        
        Args:
            query: The query to get documents for
            
        Returns:
            Empty list since no real documents are available
        """
        return [] 