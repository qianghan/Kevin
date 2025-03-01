#!/usr/bin/env python
"""
Test script for DeepSeekAPI to verify functionality.
"""

import os
import sys
from typing import Dict, Any

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Import the DeepSeekAPI class
from src.models.deepseek_client import DeepSeekAPI

def test_deepseek_api():
    """Test the DeepSeekAPI with a simple query."""
    print("Initializing DeepSeekAPI...")
    api = DeepSeekAPI()
    print(f"DeepSeekAPI initialized with model: {api.model_name}")
    
    # Test query
    query = "What are the main features of Canadian universities?"
    print(f"Testing query: {query}\n")
    
    # Test different methods to invoke the API
    methods = [
        {"name": "_call method", "func": lambda: api._call(query)},
        {"name": "invoke with string", "func": lambda: api.invoke(query)},
        {"name": "invoke with dict (input key)", "func": lambda: api.invoke({"input": query})},
        {"name": "invoke with dict (prompt key)", "func": lambda: api.invoke({"prompt": query})},
    ]
    
    successful_methods = []
    
    for method in methods:
        print(f"\nTesting {method['name']}...")
        try:
            response = method["func"]()
            print("Response:")
            print("-" * 80)
            if isinstance(response, dict):
                print(response.get("output", "No output key in response"))
            else:
                print(response)
            print("-" * 80)
            print(f"{method['name']} test completed successfully!")
            successful_methods.append(method["name"])
        except Exception as e:
            print(f"Error using {method['name']}: {e}")
    
    if not successful_methods:
        print("\nAll methods failed. Please check the DeepSeekAPI implementation and LangChain version.")
    else:
        print(f"\nDeepSeekAPI test completed successfully with {len(successful_methods)}/{len(methods)} methods!")
        print(f"Successful methods: {', '.join(successful_methods)}")

if __name__ == "__main__":
    test_deepseek_api() 