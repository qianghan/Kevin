from typing import Any, Dict, List, Optional
import httpx
from pydantic import BaseModel

from .client import DeepSeekClient, DeepSeekRequest, DeepSeekResponse

class V3Response(DeepSeekResponse):
    """Response model for DeepSeek V3 API"""
    choices: List[Dict[str, Any]] = Field(..., description="Generated choices")
    created: int = Field(..., description="Timestamp of creation")
    id: str = Field(..., description="Response ID")

class V3Request(DeepSeekRequest):
    """Request model for DeepSeek V3 API"""
    messages: List[Dict[str, str]] = Field(..., description="Message history")
    stream: bool = Field(default=False, description="Whether to stream the response")
    functions: Optional[List[Dict[str, Any]]] = Field(default=None, description="Available functions")
    function_call: Optional[str] = Field(default=None, description="Function call mode")

class DeepSeekV3(DeepSeekClient):
    """Client for DeepSeek V3 API with real-time capabilities"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "deepseek-ai/deepseek-v3",
        base_url: str = "https://api.deepseek.com/v1",
        timeout: int = 30
    ):
        super().__init__(api_key, model, base_url, timeout)
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        )
    
    async def generate(
        self,
        prompt: str,
        **kwargs: Any
    ) -> DeepSeekResponse:
        """Generate content from a prompt"""
        try:
            # Prepare messages
            messages = [{"role": "user", "content": prompt}]
            if "context" in kwargs:
                messages.insert(0, {"role": "system", "content": str(kwargs["context"])})
            
            # Prepare request
            request = V3Request(
                messages=messages,
                model=self.model,
                **kwargs
            )
            
            # Make API call
            response = await self._client.post(
                "/chat/completions",
                json=request.model_dump(exclude_none=True)
            )
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            return self._validate_response(data)
            
        except Exception as e:
            self._handle_error(e)
    
    async def generate_batch(
        self,
        prompts: List[str],
        **kwargs: Any
    ) -> List[DeepSeekResponse]:
        """Generate content from multiple prompts"""
        tasks = [self.generate(prompt, **kwargs) for prompt in prompts]
        return await asyncio.gather(*tasks)
    
    async def analyze(
        self,
        text: str,
        task: str,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Analyze text for a specific task"""
        try:
            # Prepare system message
            system_message = f"You are an AI assistant specialized in {task}. "
            system_message += "Analyze the following text and provide detailed insights."
            
            # Prepare messages
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": text}
            ]
            
            # Prepare request
            request = V3Request(
                messages=messages,
                model=self.model,
                temperature=0.3,  # Lower temperature for analysis
                **kwargs
            )
            
            # Make API call
            response = await self._client.post(
                "/chat/completions",
                json=request.model_dump(exclude_none=True)
            )
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            return {
                "analysis": data["choices"][0]["message"]["content"],
                "confidence": self._calculate_confidence(data),
                "metadata": {
                    "model": self.model,
                    "usage": data["usage"],
                    "finish_reason": data["choices"][0]["finish_reason"]
                }
            }
            
        except Exception as e:
            self._handle_error(e)
    
    async def stream_generate(
        self,
        prompt: str,
        **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """Stream generated content"""
        try:
            # Prepare messages
            messages = [{"role": "user", "content": prompt}]
            if "context" in kwargs:
                messages.insert(0, {"role": "system", "content": str(kwargs["context"])})
            
            # Prepare request
            request = V3Request(
                messages=messages,
                model=self.model,
                stream=True,
                **kwargs
            )
            
            # Make streaming API call
            async with self._client.stream(
                "POST",
                "/chat/completions",
                json=request.model_dump(exclude_none=True)
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            if data["choices"][0]["delta"].get("content"):
                                yield data["choices"][0]["delta"]["content"]
                        except json.JSONDecodeError:
                            continue
            
        except Exception as e:
            self._handle_error(e)
    
    def _calculate_confidence(self, data: Dict[str, Any]) -> float:
        """Calculate confidence score from response data"""
        # This is a simple implementation - you might want to make it more sophisticated
        if data["choices"][0]["finish_reason"] == "stop":
            return 1.0
        return 0.8
    
    async def close(self) -> None:
        """Close the HTTP client"""
        await self._client.aclose()
    
    async def __aenter__(self) -> "DeepSeekV3":
        """Context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit"""
        await self.close() 