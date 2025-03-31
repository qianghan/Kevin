"""
Tests for the DeepSeek R1 API client.

This module tests:
- Client initialization
- Content generation
- Batch processing
- Document analysis
- Error handling
"""

import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock

from profiler.app.backend.core.deepseek.r1 import DeepSeekR1, R1Request, R1Response


class TestDeepSeekR1:
    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test client initialization with config values."""
        with patch('profiler.app.backend.core.deepseek.r1.get_deepseek_config') as mock_config:
            # Setup mock config values
            mock_config.side_effect = lambda key, default=None: {
                "api_key": "test_api_key",
                "url": "https://test-api.example.com",
                "model": "test-model",
                "batch_size": 3,
                "max_tokens": 1000,
                "temperature": 0.5,
                "timeout": 20
            }.get(key, default)
            
            # Initialize client
            client = DeepSeekR1()
            
            # Check configuration was applied
            assert client.api_key == "test_api_key"
            assert client.base_url == "https://test-api.example.com"
            assert client.model == "test-model"
            assert client.max_batch_size == 3
            assert client.default_max_tokens == 1000
            assert client.default_temperature == 0.5
            assert client.timeout == 20
    
    @pytest.mark.asyncio
    async def test_generate(self, mock_deepseek_client):
        """Test generating content from a prompt."""
        # Mock the _post method to return a specific response
        with patch.object(
            mock_deepseek_client, '_post', 
            return_value={"outputs": ["Generated text response"], "batch_size": 1}
        ) as mock_post:
            response = await mock_deepseek_client.generate(
                "What is machine learning?",
                max_tokens=500,
                temperature=0.7
            )
            
            # Check the response structure
            assert "text" in response
            assert "confidence" in response
            assert "raw_response" in response
            assert response["text"] == "Generated text response"
            
            # Verify the request was properly formed
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            assert args[0] == f"/models/{mock_deepseek_client.model}/generate"
            assert "inputs" in kwargs[0]
            assert kwargs[0]["inputs"] == ["What is machine learning?"]
            assert kwargs[0]["parameters"]["max_tokens"] == 500
            assert kwargs[0]["parameters"]["temperature"] == 0.7
    
    @pytest.mark.asyncio
    async def test_generate_with_error(self, mock_deepseek_client):
        """Test error handling during content generation."""
        # Mock the _post method to return an error
        with patch.object(
            mock_deepseek_client, '_post',
            return_value={"error": "API rate limit exceeded"}
        ) as mock_post:
            # Should raise an exception
            with pytest.raises(Exception) as excinfo:
                await mock_deepseek_client.generate("Test prompt")
            
            assert "API error" in str(excinfo.value)
            assert "rate limit" in str(excinfo.value)
    
    @pytest.mark.asyncio
    async def test_generate_batch(self, mock_deepseek_client):
        """Test generating content from multiple prompts in batches."""
        # Create test prompts
        prompts = [f"Prompt {i}" for i in range(7)]  # 7 prompts
        
        # Mock responses for each batch
        batch_responses = [
            # First batch (5 prompts)
            {"outputs": [f"Response for Prompt {i}" for i in range(5)], "batch_size": 5},
            # Second batch (2 prompts)
            {"outputs": [f"Response for Prompt {i}" for i in range(5, 7)], "batch_size": 2}
        ]
        
        # Mock the _post method to return the responses
        with patch.object(
            mock_deepseek_client, '_post',
            side_effect=batch_responses
        ) as mock_post:
            responses = await mock_deepseek_client.generate_batch(
                prompts,
                max_tokens=200,
                temperature=0.8
            )
            
            # Check responses
            assert len(responses) == 7
            for i, response in enumerate(responses):
                assert response["text"] == f"Response for Prompt {i}"
                assert "confidence" in response
            
            # Check that _post was called twice (for two batches)
            assert mock_post.call_count == 2
            
            # Check first batch
            args1, kwargs1 = mock_post.call_args_list[0]
            assert len(kwargs1[0]["inputs"]) == 5
            
            # Check second batch
            args2, kwargs2 = mock_post.call_args_list[1]
            assert len(kwargs2[0]["inputs"]) == 2
    
    @pytest.mark.asyncio
    async def test_generate_batch_with_error(self, mock_deepseek_client):
        """Test error handling in batch generation."""
        prompts = ["Prompt 1", "Prompt 2", "Prompt 3"]
        
        # Mock the _post method to return an error
        with patch.object(
            mock_deepseek_client, '_post',
            return_value={"error": "Server error"}
        ) as mock_post:
            responses = await mock_deepseek_client.generate_batch(prompts)
            
            # Should return error responses for each prompt
            assert len(responses) == 3
            for response in responses:
                assert response["text"] == ""
                assert response["confidence"] == 0
                assert "error" in response
    
    @pytest.mark.asyncio
    async def test_analyze(self, mock_deepseek_client):
        """Test analyzing text content."""
        # Mock the _post method to return a specific response
        with patch.object(
            mock_deepseek_client, '_post',
            return_value={
                "outputs": ['{"sentiment": "positive", "topics": ["education", "technology"]}'],
                "batch_size": 1
            }
        ) as mock_post:
            response = await mock_deepseek_client.analyze(
                "I love learning about new technologies in education.",
                analysis_type="sentiment"
            )
            
            # Check response structure
            assert "analysis" in response
            assert "confidence" in response
            assert "raw_response" in response
            assert response["analysis"]["sentiment"] == "positive"
            assert "education" in response["analysis"]["topics"]
            
            # Verify request format
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            assert "analysis_type" in kwargs[0]["parameters"]["system_prompt"]
            assert kwargs[0]["parameters"]["temperature"] == 0.2  # Lower temp for analysis
    
    @pytest.mark.asyncio
    async def test_analyze_with_invalid_json(self, mock_deepseek_client):
        """Test handling invalid JSON in analysis response."""
        # Mock response with text that isn't valid JSON
        with patch.object(
            mock_deepseek_client, '_post',
            return_value={
                "outputs": ["This is not valid JSON"],
                "batch_size": 1
            }
        ) as mock_post:
            response = await mock_deepseek_client.analyze("Some text")
            
            # Should handle gracefully and return the raw text
            assert "analysis" in response
            assert "raw_analysis" in response["analysis"]
            assert response["analysis"]["raw_analysis"] == "This is not valid JSON"
    
    @pytest.mark.asyncio
    async def test_process_documents(self, mock_deepseek_client):
        """Test processing multiple documents."""
        # Test documents
        documents = [
            {"id": "doc1", "type": "transcript", "content": "Student transcript content"},
            {"id": "doc2", "type": "essay", "content": "Essay content"}
        ]
        
        # Mock generate_batch to return specific responses
        with patch.object(
            mock_deepseek_client, 'generate_batch',
            return_value=[
                {"text": "Transcript analysis", "confidence": 0.9},
                {"text": "Essay analysis", "confidence": 0.85}
            ]
        ) as mock_generate:
            results = await mock_deepseek_client.process_documents(documents)
            
            # Check results
            assert len(results) == 2
            assert results[0]["document_id"] == "doc1"
            assert results[0]["document_type"] == "transcript"
            assert results[0]["text"] == "Transcript analysis"
            
            assert results[1]["document_id"] == "doc2"
            assert results[1]["document_type"] == "essay"
            assert results[1]["text"] == "Essay analysis"
            
            # Verify generate_batch was called with appropriate prompts
            mock_generate.assert_called_once()
            args, kwargs = mock_generate.call_args
            assert len(args[0]) == 2  # Two prompts
            assert "transcript" in args[0][0].lower()
            assert "essay" in args[0][1].lower()
    
    @pytest.mark.asyncio
    async def test_process_documents_empty(self, mock_deepseek_client):
        """Test processing an empty document list."""
        results = await mock_deepseek_client.process_documents([])
        assert results == []
    
    def test_calculate_confidence(self, mock_deepseek_client):
        """Test confidence calculation for different response types."""
        # Text output
        confidence1 = mock_deepseek_client._calculate_confidence(
            {"outputs": ["This is a short response"]}
        )
        assert 0.7 <= confidence1 < 1.0
        
        # Longer text should have higher confidence
        confidence2 = mock_deepseek_client._calculate_confidence(
            {"outputs": ["This is a much longer response " * 10]}
        )
        assert confidence1 < confidence2
        
        # Structured output
        confidence3 = mock_deepseek_client._calculate_confidence(
            {"outputs": [{"structured": "data"}]}
        )
        assert confidence3 == 0.85
        
        # Empty output
        confidence4 = mock_deepseek_client._calculate_confidence(
            {"outputs": []}
        )
        assert confidence4 == 0.0
        
        # Error case should default to 0.5
        confidence5 = mock_deepseek_client._calculate_confidence(
            "not a valid response object"
        )
        assert confidence5 == 0.5


# Test R1Request model
def test_r1_request_model():
    """Test the R1Request model structure."""
    # Basic request
    request = R1Request(
        inputs=["What is AI?"],
        parameters={"max_tokens": 100, "temperature": 0.7},
        batch_size=1
    )
    
    # Validate serialization
    request_json = json.loads(request.model_dump_json())
    assert request_json["inputs"] == ["What is AI?"]
    assert request_json["parameters"]["max_tokens"] == 100
    assert request_json["batch_size"] == 1
    
    # Default values
    request2 = R1Request(inputs=["Test"])
    assert request2.parameters == {}
    assert request2.batch_size is None


# Test R1Response model
def test_r1_response_model():
    """Test the R1Response model structure."""
    # Text outputs
    response1 = R1Response(
        outputs=["Response 1", "Response 2"],
        batch_size=2
    )
    assert response1.outputs == ["Response 1", "Response 2"]
    assert response1.batch_size == 2
    
    # JSON outputs
    response2 = R1Response(
        outputs=[{"key1": "value1"}, {"key2": "value2"}],
        batch_size=2
    )
    assert response2.outputs[0]["key1"] == "value1"
    assert response2.outputs[1]["key2"] == "value2" 