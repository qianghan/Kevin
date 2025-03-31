"""
DeepSeek R1 API client implementation.

This module provides an implementation of the AIClientInterface
for the DeepSeek R1 API.
"""

import asyncio
import json
import re
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel

from ...utils.logging import get_logger
from ...utils.errors import APIClientError, ValidationError
from ...utils.config_manager import ConfigManager
from ..interfaces import AIClientInterface
from .client import DeepSeekClient

logger = get_logger(__name__)
config = ConfigManager().get_config().get("ai_clients", {}).get("deepseek", {})

class R1Response(BaseModel):
    """Model representing a response from the DeepSeek R1 API."""
    outputs: Union[List[str], List[Dict[str, Any]]]
    batch_size: int

class R1Request(BaseModel):
    """Model representing a request to the DeepSeek R1 API."""
    inputs: Union[List[str], List[Dict[str, Any]]]
    parameters: Dict[str, Any] = {}
    batch_size: Optional[int] = None

class DeepSeekR1(DeepSeekClient, AIClientInterface):
    """
    Client for the DeepSeek R1 API.
    
    This client implements the AIClientInterface for the DeepSeek R1 API,
    providing methods for generating content, analyzing text, and processing documents.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize the DeepSeek R1 client.
        
        Args:
            api_key: API key for authentication. If None, fetched from config.
            base_url: Base URL for the API. If None, fetched from config.
        """
        # Get values from config if not provided
        _api_key = api_key or config.get("api_key")
        _base_url = base_url or config.get("url")
        
        if not _api_key or not _base_url:
            logger.error("Missing API key or base URL for DeepSeek R1 client")
            raise ValidationError("Missing API key or base URL for DeepSeek R1 client")
        
        self.model = config.get("model", "r1-alpha")
        self.max_batch_size = config.get("batch_size", 5)
        self.default_max_tokens = config.get("max_tokens", 2000)
        self.default_temperature = config.get("temperature", 0.7)
        self.timeout = config.get("timeout", 30)
        self._initialized = False
        
        super().__init__(api_key=_api_key, base_url=_base_url)
        logger.info(f"Initialized DeepSeekR1 client with model {self.model}")
    
    async def initialize(self) -> None:
        """Initialize the client and verify connectivity."""
        try:
            logger.info("Initializing DeepSeekR1 client")
            
            # Verify connection with a simple ping
            response = await self._get("/status")
            if not response.get("status") == "ok":
                logger.error(f"Failed to connect to DeepSeek API: {response}")
                raise APIClientError("Failed to connect to DeepSeek API")
            
            self._initialized = True
            logger.info("DeepSeekR1 client initialized successfully")
        except Exception as e:
            logger.exception(f"Error initializing DeepSeekR1 client: {str(e)}")
            raise APIClientError(f"Failed to initialize DeepSeekR1 client: {str(e)}")
    
    async def shutdown(self) -> None:
        """Shutdown the client and release resources."""
        logger.info("Shutting down DeepSeekR1 client")
        # Nothing to do for this implementation
        self._initialized = False
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text based on a prompt.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional parameters for the generation
            
        Returns:
            Generated text as a string
            
        Raises:
            APIClientError: If the API call fails
        """
        try:
            if not self._initialized:
                await self.initialize()
            
            result = await self.generate(prompt, **kwargs)
            return result["text"]
        except Exception as e:
            logger.exception(f"Error generating text: {str(e)}")
            raise APIClientError(f"Failed to generate text: {str(e)}")
    
    async def generate_structured_output(
        self, 
        messages: List[Dict[str, str]], 
        response_schema: Dict[str, Any],
        **kwargs
    ) -> Any:
        """
        Generate structured output based on a prompt, conforming to a schema.
        
        Args:
            messages: List of message dictionaries with role and content
            response_schema: JSON schema for the expected response
            **kwargs: Additional parameters for the generation
            
        Returns:
            Structured output conforming to the schema
            
        Raises:
            APIClientError: If the API call fails
            ValidationError: If the generated output does not conform to the schema
        """
        try:
            if not self._initialized:
                await self.initialize()
            
            # Format messages into a prompt
            prompt = self._format_messages(messages)
            
            # Add schema to the prompt
            schema_prompt = f"""
Please generate a response that strictly conforms to the following JSON schema:
```json
{json.dumps(response_schema, indent=2)}
```

Your response should be valid JSON and nothing else. Do not include any explanations or text outside the JSON.
"""
            full_prompt = f"{prompt}\n\n{schema_prompt}"
            
            # Set parameters optimized for JSON generation
            params = {
                "max_tokens": kwargs.pop("max_tokens", self.default_max_tokens),
                "temperature": kwargs.pop("temperature", 0.2),  # Lower temperature for structured output
                **kwargs
            }
            
            # Generate the response
            result = await self.generate(full_prompt, **params)
            text_response = result["text"]
            
            # Extract JSON from the response
            json_match = re.search(r'([\s\S]*?)(```(?:json)?)?([{[][\s\S]*?[}\]])(```)?', text_response)
            if json_match:
                json_str = json_match.group(3)
            else:
                json_str = text_response
            
            # Clean up any remaining markdown or text
            json_str = re.sub(r'```(?:json)?\s*', '', json_str)
            json_str = re.sub(r'\s*```', '', json_str)
            
            # Parse the JSON
            try:
                parsed_data = json.loads(json_str)
                return parsed_data
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Raw response: {text_response}")
                raise ValidationError(f"Failed to parse structured output: {str(e)}")
            
        except (json.JSONDecodeError, ValidationError) as e:
            # Re-raise validation errors
            logger.error(f"Validation error in structured output: {str(e)}")
            raise ValidationError(f"Invalid structured output: {str(e)}")
        except Exception as e:
            logger.exception(f"Error generating structured output: {str(e)}")
            raise APIClientError(f"Failed to generate structured output: {str(e)}")
    
    async def extract_data(
        self,
        text: str,
        data_schema: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Extract structured data from text.
        
        Args:
            text: The input text to extract data from
            data_schema: JSON schema for the expected data structure
            **kwargs: Additional parameters for the extraction
            
        Returns:
            Extracted data as a dictionary
            
        Raises:
            APIClientError: If the extraction fails
        """
        try:
            if not self._initialized:
                await self.initialize()
            
            # Create a prompt for data extraction
            prompt = f"""
Extract the structured data from the following text according to the specified schema:

Text to analyze:
```
{text}
```

Output schema:
```json
{json.dumps(data_schema, indent=2)}
```

Extract all relevant information and provide it in a valid JSON format that matches the schema.
"""
            
            # Generate structured output
            result = await self.generate_structured_output(
                messages=[
                    {"role": "system", "content": "You are a data extraction assistant."},
                    {"role": "user", "content": prompt}
                ],
                response_schema=data_schema,
                **kwargs
            )
            
            return result
        except ValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.exception(f"Error extracting data: {str(e)}")
            raise APIClientError(f"Failed to extract data: {str(e)}")
    
    async def classify_text(
        self,
        text: str,
        categories: List[str],
        **kwargs
    ) -> Dict[str, float]:
        """
        Classify text into one or more categories.
        
        Args:
            text: The input text to classify
            categories: List of possible categories
            **kwargs: Additional parameters for the classification
            
        Returns:
            Dictionary mapping categories to confidence scores
            
        Raises:
            APIClientError: If the classification fails
        """
        try:
            if not self._initialized:
                await self.initialize()
            
            # Create a prompt for classification
            categories_str = ", ".join(categories)
            prompt = f"""
Classify the following text into one or more of these categories: {categories_str}
Respond with a JSON object mapping each category to a confidence score between 0.0 and 1.0.
Only include categories with non-zero confidence scores.

Text to classify:
```
{text}
```
"""
            
            # Define the schema
            schema = {
                "type": "object",
                "properties": {
                    cat: {"type": "number", "minimum": 0, "maximum": 1}
                    for cat in categories
                },
                "additionalProperties": False
            }
            
            # Generate structured output
            result = await self.generate_structured_output(
                messages=[
                    {"role": "system", "content": "You are a text classification assistant."},
                    {"role": "user", "content": prompt}
                ],
                response_schema=schema,
                **kwargs
            )
            
            # Ensure all categories have a value
            classification = {cat: result.get(cat, 0.0) for cat in categories}
            return classification
        except ValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.exception(f"Error classifying text: {str(e)}")
            raise APIClientError(f"Failed to classify text: {str(e)}")
    
    async def analyze_document(
        self,
        document: str,
        document_type: str,
        analysis_type: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Analyze a document and extract insights.
        
        Args:
            document: The document content
            document_type: Type of document (e.g., "resume", "cover_letter")
            analysis_type: Type of analysis to perform
            **kwargs: Additional parameters for the analysis
            
        Returns:
            Analysis results as a dictionary
            
        Raises:
            APIClientError: If the analysis fails
        """
        try:
            if not self._initialized:
                await self.initialize()
            
            # Define the schema based on analysis type
            if analysis_type == "resume":
                schema = {
                    "type": "object",
                    "properties": {
                        "personal_info": {"type": "object"},
                        "education": {"type": "array", "items": {"type": "object"}},
                        "experience": {"type": "array", "items": {"type": "object"}},
                        "skills": {"type": "array", "items": {"type": "string"}},
                        "strengths": {"type": "array", "items": {"type": "string"}},
                        "weaknesses": {"type": "array", "items": {"type": "string"}},
                        "summary": {"type": "string"}
                    }
                }
            elif analysis_type == "cover_letter":
                schema = {
                    "type": "object",
                    "properties": {
                        "tone": {"type": "string"},
                        "main_arguments": {"type": "array", "items": {"type": "string"}},
                        "qualifications": {"type": "array", "items": {"type": "string"}},
                        "strengths": {"type": "array", "items": {"type": "string"}},
                        "relevance_to_position": {"type": "number", "minimum": 0, "maximum": 1},
                        "recommendations": {"type": "array", "items": {"type": "string"}},
                        "summary": {"type": "string"}
                    }
                }
            else:
                schema = {
                    "type": "object",
                    "properties": {
                        "key_points": {"type": "array", "items": {"type": "string"}},
                        "entities": {"type": "object"},
                        "sentiment": {"type": "string"},
                        "summary": {"type": "string"}
                    }
                }
            
            # Create a prompt for document analysis
            prompt = f"""
Analyze the following {document_type} document using {analysis_type} analysis:

Document content:
```
{document}
```

Provide a comprehensive analysis with all relevant details structured according to the schema.
"""
            
            # Generate structured output
            result = await self.generate_structured_output(
                messages=[
                    {"role": "system", "content": f"You are an expert {document_type} analyst."},
                    {"role": "user", "content": prompt}
                ],
                response_schema=schema,
                **kwargs
            )
            
            return {
                "analysis": result,
                "document_type": document_type,
                "analysis_type": analysis_type
            }
        except ValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.exception(f"Error analyzing document: {str(e)}")
            raise APIClientError(f"Failed to analyze document: {str(e)}")
    
    async def generate_embeddings(
        self,
        texts: List[str],
        **kwargs
    ) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of texts to generate embeddings for
            **kwargs: Additional parameters for embedding generation
            
        Returns:
            List of embedding vectors
            
        Raises:
            APIClientError: If embedding generation fails
        """
        try:
            if not self._initialized:
                await self.initialize()
            
            # NOTE: Since DeepSeek R1 doesn't directly support embeddings,
            # this is a placeholder implementation that would need to be
            # replaced with actual embedding functionality or integration
            # with a suitable embedding model.
            logger.warning("Embedding generation is not directly supported by DeepSeek R1")
            
            # Return placeholder embeddings of dimensionality 384
            return [[0.0] * 384 for _ in texts]
        except Exception as e:
            logger.exception(f"Error generating embeddings: {str(e)}")
            raise APIClientError(f"Failed to generate embeddings: {str(e)}")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a chat completion response.
        
        Args:
            messages: List of message dictionaries with role and content
            **kwargs: Additional parameters for the completion
            
        Returns:
            Chat completion response
            
        Raises:
            APIClientError: If the chat completion fails
        """
        try:
            if not self._initialized:
                await self.initialize()
            
            # Format messages into a prompt
            prompt = self._format_messages(messages)
            
            # Generate response
            result = await self.generate(prompt, **kwargs)
            
            return {
                "text": result["text"],
                "finish_reason": "stop",
                "confidence": result.get("confidence", 0.0)
            }
        except Exception as e:
            logger.exception(f"Error generating chat completion: {str(e)}")
            raise APIClientError(f"Failed to generate chat completion: {str(e)}")
    
    async def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Generate content from a prompt (internal implementation).
        
        Args:
            prompt: The prompt to generate content from.
            **kwargs: Additional parameters to pass to the API.
            
        Returns:
            Response data from the API.
            
        Raises:
            APIClientError: If the API call fails
        """
        max_tokens = kwargs.pop("max_tokens", self.default_max_tokens)
        temperature = kwargs.pop("temperature", self.default_temperature)

        params = {
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs
        }
        
        request = R1Request(
            inputs=[prompt],
            parameters=params
        )
        
        try:
            endpoint = f"/models/{self.model}/generate"
            response = await self._post(endpoint, json.loads(request.model_dump_json()))
            
            if response.get("error"):
                logger.error(f"Error generating content: {response['error']}")
                raise APIClientError(f"API error: {response['error']}")
            
            response_data = R1Response(**response)
            confidence = self._calculate_confidence(response_data)
            
            return {
                "text": response_data.outputs[0] if response_data.outputs else "",
                "confidence": confidence,
                "raw_response": response
            }
        except Exception as e:
            logger.exception(f"Error calling DeepSeek API: {str(e)}")
            raise APIClientError(f"Failed to call DeepSeek API: {str(e)}")
    
    def _calculate_confidence(self, response_data: Any) -> float:
        """
        Calculate a confidence score for the response.
        
        Args:
            response_data: Response data from the API.
            
        Returns:
            Confidence score between 0.0 and 1.0.
        """
        # Simple heuristic for confidence calculation
        # In a real implementation, this would be more sophisticated
        if not response_data or not getattr(response_data, "outputs", None):
            return 0.0
        
        outputs = response_data.outputs
        if not outputs:
            return 0.0
        
        # If there's no text, confidence is 0
        if not outputs[0]:
            return 0.0
        
        # Calculate confidence based on output length (simple heuristic)
        text = outputs[0] if isinstance(outputs[0], str) else json.dumps(outputs[0])
        text_length = len(text)
        
        # Normalize to a value between 0.5 and 0.95
        # This is a very simple heuristic - a real implementation would be more nuanced
        normalized_length = min(text_length / 1000, 1.0)  # Scale by 1000 chars
        confidence = 0.5 + (normalized_length * 0.45)
        
        return confidence
    
    def _format_messages(self, messages: List[Dict[str, str]]) -> str:
        """
        Format chat messages into a prompt string.
        
        Args:
            messages: List of message dictionaries with role and content
            
        Returns:
            Formatted prompt string
        """
        system_content = None
        formatted_messages = []
        
        for message in messages:
            role = message.get("role", "").lower()
            content = message.get("content", "")
            
            if role == "system":
                system_content = content
            elif role == "user":
                formatted_messages.append(f"User: {content}")
            elif role == "assistant":
                formatted_messages.append(f"Assistant: {content}")
            else:
                formatted_messages.append(f"{role.capitalize()}: {content}")
        
        # Add system content at the beginning if available
        if system_content:
            prompt = f"System: {system_content}\n\n" + "\n\n".join(formatted_messages)
        else:
            prompt = "\n\n".join(formatted_messages)
        
        # Add a final assistant prefix to indicate where model should continue
        if not prompt.endswith("Assistant: "):
            prompt += "\n\nAssistant: "
            
        return prompt
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.shutdown() 