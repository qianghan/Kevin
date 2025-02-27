"""
DeepSeek API client for integration with LangChain.
"""

import os
import sys
import json
import requests
import yaml
import time
from typing import Any, Dict, List, Mapping, Optional
from dotenv import load_dotenv
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.llms.base import LLM

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import project modules
from src.utils.logger import get_logger, api_logger

# Load environment variables
load_dotenv()

# Configure module logger
logger = get_logger(__name__)

class DeepSeekAPI(LLM):
    """LangChain compatible client for the DeepSeek API."""
    
    api_key: str
    model_name: str = "deepseek-chat"
    temperature: float = 0.1
    max_tokens: int = 1000
    top_p: float = 0.95
    api_base: str = "https://api.deepseek.com/v1"
    request_timeout: int = 60
    max_retries: int = 3
    retry_delay: int = 2
    
    def __init__(self, **kwargs):
        """Initialize the DeepSeek API client."""
        # Load config if provided or use defaults/env vars
        config_path = kwargs.pop("config_path", "config.yaml")
        
        logger.info(f"Initializing DeepSeek API client using config from {config_path}")
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
                llm_config = config.get('llm', {})
                
                # Set API key from config or environment variable
                api_key = llm_config.get('api_key', '')
                if not api_key:
                    api_key = os.getenv('DEEPSEEK_API_KEY', '')
                    logger.debug("Using API key from environment variable")
                else:
                    logger.debug("Using API key from config file")
                
                kwargs.setdefault('api_key', api_key)
                kwargs.setdefault('model_name', llm_config.get('model_name', self.model_name))
                kwargs.setdefault('temperature', llm_config.get('temperature', self.temperature))
                kwargs.setdefault('max_tokens', llm_config.get('max_tokens', self.max_tokens))
                
                # Set additional parameters from config if available
                if 'request_timeout' in llm_config:
                    kwargs.setdefault('request_timeout', llm_config.get('request_timeout'))
                if 'max_retries' in llm_config:
                    kwargs.setdefault('max_retries', llm_config.get('max_retries'))
        else:
            # Use environment variable if no config file
            logger.warning(f"Config file {config_path} not found, using environment variables")
            kwargs.setdefault('api_key', os.getenv('DEEPSEEK_API_KEY', ''))
        
        super().__init__(**kwargs)
        
        logger.info(f"DeepSeek API client initialized with model {self.model_name}")
        
        if not self.api_key:
            error_msg = "DeepSeek API key not found. Please set it in config.yaml or as DEEPSEEK_API_KEY environment variable."
            logger.critical(error_msg)
            raise ValueError(error_msg)
    
    @property
    def _llm_type(self) -> str:
        return "deepseek"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs
    ) -> str:
        """Call the DeepSeek API with the given prompt."""
        # Log the API call
        prompt_preview = prompt[:100] + "..." if len(prompt) > 100 else prompt
        api_logger.info(f"DeepSeek API call: {prompt_preview}")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Prepare request data
        data = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p
        }
        
        # Add stop sequences if provided
        if stop:
            data["stop"] = stop
        
        # Add any additional parameters
        for key, value in kwargs.items():
            data[key] = value
        
        # Implement retry logic
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(f"Making API request to DeepSeek, attempt {attempt}/{self.max_retries}")
                
                # Make API request
                response = requests.post(
                    f"{self.api_base}/chat/completions",
                    headers=headers,
                    data=json.dumps(data),
                    timeout=self.request_timeout
                )
                
                # Handle API response
                if response.status_code != 200:
                    error_msg = f"DeepSeek API request failed with status code {response.status_code}"
                    try:
                        error_data = response.json()
                        if "error" in error_data:
                            error_msg += f": {error_data['error']}"
                    except:
                        error_msg += f": {response.text}"
                    
                    logger.error(error_msg)
                    
                    # If this is the last attempt, raise the error
                    if attempt == self.max_retries:
                        api_logger.error(f"API call failed after {self.max_retries} attempts: {error_msg}")
                        raise ValueError(error_msg)
                    
                    # Otherwise, wait and retry
                    wait_time = self.retry_delay * attempt
                    logger.warning(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                
                # Extract and return the generated text
                try:
                    response_data = response.json()
                    result = response_data["choices"][0]["message"]["content"]
                    result_preview = result[:100] + "..." if len(result) > 100 else result
                    api_logger.info(f"DeepSeek API response received: {result_preview}")
                    logger.debug("API call successful")
                    return result
                except (KeyError, IndexError) as e:
                    error_msg = f"Failed to parse DeepSeek API response: {e}"
                    logger.error(error_msg)
                    if attempt == self.max_retries:
                        api_logger.error(f"Failed to parse API response after {self.max_retries} attempts: {error_msg}")
                        raise ValueError(error_msg)
                    
                    wait_time = self.retry_delay * attempt
                    logger.warning(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
            
            except requests.RequestException as e:
                logger.error(f"Request exception: {str(e)}")
                if attempt == self.max_retries:
                    api_logger.error(f"API call failed after {self.max_retries} attempts due to request exception: {str(e)}")
                    raise ValueError(f"DeepSeek API request failed: {str(e)}")
                
                wait_time = self.retry_delay * attempt
                logger.warning(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
        
        # We should never reach here due to the raises above
        error_msg = "Unexpected error in DeepSeek API call"
        logger.critical(error_msg)
        raise RuntimeError(error_msg)
    
    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for the given text using DeepSeek's embedding API."""
        api_logger.info(f"Getting embedding for text: {text[:50]}...")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Prepare request data
        data = {
            "model": "deepseek-embedding",
            "input": text
        }
        
        # Implement retry logic
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(f"Making embedding API request to DeepSeek, attempt {attempt}/{self.max_retries}")
                
                # Make API request
                response = requests.post(
                    f"{self.api_base}/embeddings",
                    headers=headers,
                    data=json.dumps(data),
                    timeout=self.request_timeout
                )
                
                # Handle API response
                if response.status_code != 200:
                    error_msg = f"DeepSeek embedding API request failed with status code {response.status_code}"
                    try:
                        error_data = response.json()
                        if "error" in error_data:
                            error_msg += f": {error_data['error']}"
                    except:
                        error_msg += f": {response.text}"
                    
                    logger.error(error_msg)
                    
                    # If this is the last attempt, raise the error
                    if attempt == self.max_retries:
                        api_logger.error(f"Embedding API call failed after {self.max_retries} attempts: {error_msg}")
                        raise ValueError(error_msg)
                    
                    # Otherwise, wait and retry
                    wait_time = self.retry_delay * attempt
                    logger.warning(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                
                # Extract and return the embedding
                try:
                    response_data = response.json()
                    embedding = response_data["data"][0]["embedding"]
                    api_logger.info(f"Embedding received, dimension: {len(embedding)}")
                    logger.debug("Embedding API call successful")
                    return embedding
                except (KeyError, IndexError) as e:
                    error_msg = f"Failed to parse DeepSeek embedding API response: {e}"
                    logger.error(error_msg)
                    if attempt == self.max_retries:
                        api_logger.error(f"Failed to parse embedding API response after {self.max_retries} attempts: {error_msg}")
                        raise ValueError(error_msg)
                    
                    wait_time = self.retry_delay * attempt
                    logger.warning(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
            
            except requests.RequestException as e:
                logger.error(f"Request exception in embedding API: {str(e)}")
                if attempt == self.max_retries:
                    api_logger.error(f"Embedding API call failed after {self.max_retries} attempts due to request exception: {str(e)}")
                    raise ValueError(f"DeepSeek embedding API request failed: {str(e)}")
                
                wait_time = self.retry_delay * attempt
                logger.warning(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
        
        # We should never reach here due to the raises above
        error_msg = "Unexpected error in DeepSeek embedding API call"
        logger.critical(error_msg)
        raise RuntimeError(error_msg)
    
    def _identifying_params(self) -> Mapping[str, Any]:
        """Return identifying parameters for logging."""
        return {
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p
        }

if __name__ == "__main__":
    # Example usage
    try:
        logger.info("Running DeepSeek API client example")
        deepseek = DeepSeekAPI()
        response = deepseek.invoke(
            "What are the main features of Canadian universities compared to American ones?"
        )
        logger.info(f"Response received successfully")
        print(f"Response: {response}")
    except Exception as e:
        logger.error(f"Error in example: {e}", exc_info=True)
        print(f"Error: {e}") 