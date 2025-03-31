from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

class DeepSeekResponse(BaseModel):
    """Base response model for DeepSeek API"""
    content: str = Field(..., description="The generated content")
    model: str = Field(..., description="The model used")
    usage: Dict[str, int] = Field(..., description="Token usage statistics")
    finish_reason: str = Field(..., description="Reason for completion")

class DeepSeekRequest(BaseModel):
    """Base request model for DeepSeek API"""
    prompt: str = Field(..., description="The input prompt")
    temperature: float = Field(default=0.7, description="Sampling temperature")
    max_tokens: int = Field(default=1000, description="Maximum tokens to generate")
    top_p: float = Field(default=1.0, description="Top-p sampling parameter")
    frequency_penalty: float = Field(default=0.0, description="Frequency penalty")
    presence_penalty: float = Field(default=0.0, description="Presence penalty")
    stop: Optional[List[str]] = Field(default=None, description="Stop sequences")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")

class DeepSeekClient(ABC):
    """Base class for DeepSeek API clients"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "deepseek-ai/deepseek-v3",
        base_url: str = "https://api.deepseek.com/v1",
        timeout: int = 30
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.timeout = timeout
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        **kwargs: Any
    ) -> DeepSeekResponse:
        """Generate content from a prompt"""
        pass
    
    @abstractmethod
    async def generate_batch(
        self,
        prompts: List[str],
        **kwargs: Any
    ) -> List[DeepSeekResponse]:
        """Generate content from multiple prompts"""
        pass
    
    @abstractmethod
    async def analyze(
        self,
        text: str,
        task: str,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Analyze text for a specific task"""
        pass
    
    def _prepare_request(
        self,
        prompt: str,
        **kwargs: Any
    ) -> DeepSeekRequest:
        """Prepare a request object"""
        return DeepSeekRequest(
            prompt=prompt,
            **kwargs
        )
    
    def _validate_response(
        self,
        response: Dict[str, Any]
    ) -> DeepSeekResponse:
        """Validate and parse API response"""
        return DeepSeekResponse(**response)
    
    def _handle_error(
        self,
        error: Exception
    ) -> None:
        """Handle API errors"""
        # Log error details
        print(f"DeepSeek API error: {str(error)}")
        raise error 