"""
Agent initialization module for web and test interfaces.
"""

import os
import sys
import yaml
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import project modules
from src.core.agent import UniversityAgent, build_agent
from src.utils.logger import get_logger

# Configure module logger
logger = get_logger(__name__)

# Load environment variables
load_dotenv()

def initialize_agent():
    """
    Initialize and return a UniversityAgent instance.
    This function is used by the web interface and tests.
    
    Returns:
        An initialized UniversityAgent instance or a compatible mock for testing
    """
    logger.info("Initializing agent for web interface")
    
    try:
        # Create a new agent instance
        agent = UniversityAgent()
        logger.info("University Agent initialized successfully")
        return agent
    except Exception as e:
        logger.error(f"Error initializing agent: {e}", exc_info=True)
        # For testing purposes, we might want to return a mock if the real agent can't be created
        raise RuntimeError(f"Failed to initialize agent: {e}")

def initialize_test_agent():
    """
    Initialize a simplified agent for testing purposes.
    This version avoids heavy dependencies that might cause issues in tests.
    
    Returns:
        A simplified agent for testing
    """
    from langchain.chains import LLMChain
    from langchain.prompts import PromptTemplate
    from langchain_community.llms.fake import FakeListLLM
    
    # Create a simple fake agent for testing that just returns predefined responses
    responses = [
        "This is a test response from the agent.",
        "I can help you with information about Canadian universities.",
        "University of Toronto has various programs in Computer Science."
    ]
    
    # Create a fake LLM
    fake_llm = FakeListLLM(responses=responses)
    
    # Create a simple chain with a template
    prompt = PromptTemplate(
        input_variables=["input"],
        template="Question: {input}\nAnswer: "
    )
    
    chain = LLMChain(llm=fake_llm, prompt=prompt, output_key="output")
    
    # Mock invoke method to match the format of the real agent
    def mock_invoke(query):
        result = chain.invoke({"input": query})
        # Include empty thinking steps to match the real agent's format
        return {
            "output": result["output"],
            "thinking": []
        }
    
    # Add the invoke method to the chain
    chain.invoke = mock_invoke
    
    logger.info("Initialized test agent with fake responses")
    return chain 