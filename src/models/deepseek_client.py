"""
DeepSeek API client for integration with LangChain.
"""

import os
import sys
import json
import requests
import yaml
import time
import hashlib
from typing import Any, Dict, List, Mapping, Optional, Union, ClassVar
from functools import lru_cache
from dotenv import load_dotenv
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.llms.base import LLM
from pydantic import BaseModel, Field, root_validator, model_validator
import logging

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import project modules
from utils.logger import get_logger, api_logger

# Load environment variables
load_dotenv()

# Configure module logger
logger = get_logger(__name__)

# Create a simple cache for API responses
RESPONSE_CACHE = {}
MAX_CACHE_SIZE = 100  # Maximum number of cached responses

class DeepSeekAPI(LLM, BaseModel):
    """LangChain compatible client for the DeepSeek API."""
    
    api_key: str = Field(default="")
    model_name: str = Field(default="deepseek-chat")
    temperature: float = Field(default=0.1)
    max_tokens: int = Field(default=1000)
    top_p: float = Field(default=0.95)
    api_base: str = Field(default="https://api.deepseek.com/v1")
    request_timeout: int = Field(default=60)
    max_retries: int = Field(default=3)
    retry_delay: int = Field(default=2)
    use_cache: bool = Field(default=True)  # Whether to use caching
    
    # Add class variables with proper type annotations
    EMBEDDING_CACHE: ClassVar[Dict[str, List[float]]] = {}
    
    model_config = {"arbitrary_types_allowed": True}
    
    @model_validator(mode='before')
    @classmethod
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that API key exists in environment."""
        # Load config if provided or use defaults/env vars
        config_path = values.get("config_path", "config.yaml")
        
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
                
                # Apply config values to dictionary
                values["api_key"] = api_key
                values["model_name"] = llm_config.get('model_name', values.get("model_name", "deepseek-chat"))
                values["temperature"] = llm_config.get('temperature', values.get("temperature", 0.1))
                values["max_tokens"] = llm_config.get('max_tokens', values.get("max_tokens", 1000))
                values["request_timeout"] = llm_config.get('request_timeout', values.get("request_timeout", 60))
                values["max_retries"] = llm_config.get('max_retries', values.get("max_retries", 3))
                values["retry_delay"] = llm_config.get('retry_delay', values.get("retry_delay", 2))
                values["use_cache"] = llm_config.get('use_cache', values.get("use_cache", True))
        else:
            # Use environment variable if no config file
            logger.warning(f"Config file {config_path} not found, using environment variables")
            values["api_key"] = os.getenv('DEEPSEEK_API_KEY', values.get("api_key", ""))
            
        if not values.get("api_key"):
            error_msg = "DeepSeek API key not found. Please set it in config.yaml or as DEEPSEEK_API_KEY environment variable."
            logger.critical(error_msg)
            raise ValueError(error_msg)
            
        logger.info(f"DeepSeek API client initialized with model {values.get('model_name')}")
        
        return values
    
    @property
    def _llm_type(self) -> str:
        return "deepseek"
    
    def _get_cache_key(self, prompt: str, stop: Optional[List[str]] = None, **kwargs) -> str:
        """Generate a cache key for the prompt and parameters."""
        # Create a string representation of the kwargs that affect the output
        kwargs_str = json.dumps({
            "model": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "stop": stop,
            **{k: v for k, v in kwargs.items() if k not in ["stream", "timeout"]}
        }, sort_keys=True)
        
        # Combine prompt and kwargs to create a hash
        combined = f"{prompt}|{kwargs_str}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def _manage_cache(self):
        """Manage the cache size to prevent memory issues."""
        global RESPONSE_CACHE
        if len(RESPONSE_CACHE) > MAX_CACHE_SIZE:
            # Remove oldest 20% of cache entries
            items_to_remove = int(MAX_CACHE_SIZE * 0.2)
            keys_to_remove = list(RESPONSE_CACHE.keys())[:items_to_remove]
            for key in keys_to_remove:
                del RESPONSE_CACHE[key]
            logger.debug(f"Cache pruned, removed {items_to_remove} entries")
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs
    ) -> str:
        """Call the DeepSeek API with the given prompt."""
        # Check cache first if caching is enabled
        if self.use_cache:
            cache_key = self._get_cache_key(prompt, stop, **kwargs)
            if cache_key in RESPONSE_CACHE:
                logger.debug("Using cached response")
                return RESPONSE_CACHE[cache_key]
        
        # Only log a preview of the prompt to reduce overhead
        prompt_preview = prompt[:50] + "..." if len(prompt) > 50 else prompt
        api_logger.info(f"DeepSeek API call: {prompt_preview}")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Prepare request data - use optimized settings
        data = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": kwargs.get("frequency_penalty", 0.2),
            "presence_penalty": kwargs.get("presence_penalty", 0.1)
        }
        
        # Add stop sequences if provided
        if stop:
            data["stop"] = stop
        
        # Add any additional parameters but only those that are relevant
        for key, value in kwargs.items():
            if key in ["stream", "stop", "n", "logit_bias"]:
                data[key] = value
        
        # Start timing the API call
        start_time = time.time()
        
        # Implement retry logic
        for attempt in range(1, self.max_retries + 1):
            try:
                # Only log detailed debugging information on first attempt
                if attempt == 1:
                    logger.debug(f"Making API request to DeepSeek")
                else:
                    logger.debug(f"Retrying API request, attempt {attempt}/{self.max_retries}")
                
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
                    
                    # Otherwise, wait and retry with exponential backoff
                    wait_time = self.retry_delay * (2 ** (attempt - 1))
                    logger.warning(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                
                # Extract and return the generated text
                try:
                    response_data = response.json()
                    result = response_data["choices"][0]["message"]["content"]
                    
                    # Log API performance
                    duration = time.time() - start_time
                    api_logger.info(f"DeepSeek API response received in {duration:.2f}s")
                    
                    # Log the full response content to a dedicated file
                    try:
                        # Create a responses directory if it doesn't exist
                        responses_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'responses')
                        os.makedirs(responses_dir, exist_ok=True)
                        
                        # Write response to timestamped file
                        timestamp = time.strftime("%Y%m%d-%H%M%S")
                        response_file = os.path.join(responses_dir, f'response-{timestamp}.txt')
                        
                        with open(response_file, 'w') as f:
                            f.write(f"===== DEEPSEEK RESPONSE AT {time.strftime('%Y-%m-%d %H:%M:%S')} =====\n\n")
                            f.write(result)
                            f.write("\n\n====== END OF RESPONSE ======\n")
                        
                        # Log that we saved the full response
                        logger.info(f"Full response saved to {response_file}")
                    except Exception as e:
                        logger.error(f"Failed to save response to file: {e}")
                    
                    # Only log a preview of the result to reduce overhead
                    if logger.level <= logging.DEBUG:
                        result_preview = result[:50] + "..." if len(result) > 50 else result
                        logger.debug(f"API response: {result_preview}")
                    else:
                        # Even at INFO level, log more of the content
                        logger.info(f"API response (first 500 chars): {result[:500]}...")
                    
                    # Cache the result if caching is enabled
                    if self.use_cache:
                        RESPONSE_CACHE[cache_key] = result
                        self._manage_cache()
                        
                    return result
                except (KeyError, IndexError) as e:
                    error_msg = f"Failed to parse DeepSeek API response: {e}"
                    logger.error(error_msg)
                    if attempt == self.max_retries:
                        api_logger.error(f"Failed to parse API response: {error_msg}")
                        raise ValueError(error_msg)
                    
                    # Use exponential backoff for retries
                    wait_time = self.retry_delay * (2 ** (attempt - 1))
                    logger.warning(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
            
            except requests.RequestException as e:
                logger.error(f"Request exception: {str(e)}")
                if attempt == self.max_retries:
                    api_logger.error(f"API call failed due to request exception: {str(e)}")
                    raise ValueError(f"DeepSeek API request failed: {str(e)}")
                
                # Use exponential backoff for retries
                wait_time = self.retry_delay * (2 ** (attempt - 1))
                logger.warning(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
        
        # We should never reach here due to the raises above
        error_msg = "Unexpected error in DeepSeek API call"
        logger.critical(error_msg)
        raise RuntimeError(error_msg)
    
    def invoke(self, input_data: Union[str, Dict[str, Any], List], **kwargs) -> Union[str, Dict[str, str]]:
        """
        Invoke the model with the given input.
        
        This method handles string inputs, dictionary inputs, and list inputs (for LangChain messages)
        to support both LangChain v1 and v2 interfaces.
        
        Args:
            input_data: Either a string prompt, a dictionary with an "input" key, or a list of messages
            **kwargs: Additional keyword arguments to pass to the model
            
        Returns:
            Either a string response or a dictionary with an "output" key
        """
        try:
            logger.debug(f"Invoke called with input type: {type(input_data)}")
            
            # Handle string input (LangChain v1 style)
            if isinstance(input_data, str):
                logger.info("Processing string input")
                result = self._call(input_data, **kwargs)
                logger.info(f"Generated result (string input): {result[:50]}...")
                return result
            
            # Handle list input (LangChain message list)
            elif isinstance(input_data, list):
                logger.info(f"Processing list input with {len(input_data)} items")
                # Extract text from message objects
                combined_prompt = ""
                for message in input_data:
                    if hasattr(message, "content"):
                        role = getattr(message, "type", "unknown")
                        content = message.content
                        combined_prompt += f"\n\n{role}: {content}"
                        logger.debug(f"Added message content from {role}")
                    elif isinstance(message, dict) and "content" in message:
                        role = message.get("role", "unknown")
                        content = message["content"]
                        combined_prompt += f"\n\n{role}: {content}"
                        logger.debug(f"Added dict content from {role}")
                
                if not combined_prompt:
                    raise ValueError("Could not extract content from message list")
                
                result = self._call(combined_prompt, **kwargs)
                logger.info(f"Generated result (list input): {result[:50]}...")
                
                # Return as a simple string to avoid compatibility issues
                # This ensures our agent code can handle the response directly
                logger.info("Returning result as string to ensure compatibility")
                return result
                
            # Handle dictionary input (LangChain v2 style)
            elif isinstance(input_data, dict) and "input" in input_data:
                logger.info("Processing dict input with 'input' key")
                prompt = input_data["input"]
                result = self._call(prompt, **kwargs)
                logger.info(f"Generated result (dict input): {result[:50]}...")
                return {"output": result}
                
            # Handle other dictionary formats
            elif isinstance(input_data, dict):
                logger.info(f"Processing dict input with keys: {list(input_data.keys())}")
                # Try to find a key that might contain the prompt
                for key in ["prompt", "text", "query", "message", "content"]:
                    if key in input_data:
                        prompt = input_data[key]
                        result = self._call(prompt, **kwargs)
                        logger.info(f"Generated result (dict with {key}): {result[:50]}...")
                        return {"output": result}
                
                # If we can't find a suitable key, raise an error
                raise ValueError(f"Could not find a suitable prompt key in input: {input_data.keys()}")
                
            else:
                raise ValueError(f"Unsupported input type: {type(input_data)}")
                
        except Exception as e:
            logger.error(f"Error in invoke method: {str(e)}", exc_info=True)
            # Re-raise the exception to be handled by the caller
            raise
    
    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for the given text using DeepSeek's embedding API."""
        # Check cache first
        if self.use_cache:
            cache_key = hashlib.md5(text.encode()).hexdigest()
            if cache_key in self.EMBEDDING_CACHE:
                logger.info("Using cached embedding")
                return self.EMBEDDING_CACHE[cache_key]
                
        api_logger.info(f"Getting embedding for text: {text[:50]}...")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Prepare request data
        data = {
            "model": "deepseek-embed",
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
                    
                    # Cache the embedding
                    if self.use_cache:
                        cache_key = hashlib.md5(text.encode()).hexdigest()
                        self.EMBEDDING_CACHE[cache_key] = embedding
                        # Manage embedding cache size
                        if len(self.EMBEDDING_CACHE) > MAX_CACHE_SIZE:
                            keys_to_remove = list(self.EMBEDDING_CACHE.keys())[:int(MAX_CACHE_SIZE * 0.2)]
                            for key in keys_to_remove:
                                del self.EMBEDDING_CACHE[key]
                    
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
            "top_p": self.top_p,
            "use_cache": self.use_cache
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