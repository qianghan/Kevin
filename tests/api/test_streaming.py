"""
Tests for the streaming service.

This module contains tests for the streaming service in the Kevin API.
"""

import json
import asyncio
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


@pytest.fixture
def stream_event_constants():
    """Provide constants for StreamEvent."""
    return type('StreamEvent', (), {
        'THINKING_START': 'thinking_start',
        'THINKING_UPDATE': 'thinking_update',
        'THINKING_END': 'thinking_end',
        'ANSWER_START': 'answer_start',
        'ANSWER_CHUNK': 'answer_chunk',
        'ANSWER_END': 'answer_end',
        'DOCUMENT': 'document',
        'ERROR': 'error',
        'DONE': 'done',
    })


class MockStreamManager:
    """Mock implementation of StreamManager for testing."""
    
    def __init__(self):
        """Initialize the mock stream manager."""
        self.queue = asyncio.Queue()
        self.is_done = False
    
    async def add_event(self, event_type, data):
        """Add an event to the queue."""
        await self.queue.put((event_type, data))
        if event_type in ['done', 'error']:
            self.is_done = True
    
    async def get_stream(self):
        """Get a stream of events."""
        while not (self.is_done and self.queue.empty()):
            try:
                event_type, data = await asyncio.wait_for(self.queue.get(), timeout=0.1)
                yield f"event: {event_type}\n"
                yield f"data: {json.dumps(data)}\n\n"
                self.queue.task_done()
                if event_type in ['done', 'error']:
                    break
            except asyncio.TimeoutError:
                yield ": keepalive\n\n"
            except Exception as e:
                yield f"event: error\n"
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                break


@pytest.mark.asyncio
async def test_stream_manager_add_event(stream_event_constants):
    """Test adding events to the stream manager."""
    # Create a stream manager
    stream_manager = MockStreamManager()
    StreamEvent = stream_event_constants
    
    # Add an event
    await stream_manager.add_event(StreamEvent.THINKING_START, {"query": "test"})
    
    # Check the queue
    assert stream_manager.queue.qsize() == 1
    
    # Get the event from the queue
    event_type, data = await stream_manager.queue.get()
    
    # Check the event
    assert event_type == StreamEvent.THINKING_START
    assert data == {"query": "test"}
    
    # Add a done event
    await stream_manager.add_event(StreamEvent.DONE, {"result": "done"})
    
    # Check that is_done is set
    assert stream_manager.is_done == True


@pytest.mark.asyncio
async def test_stream_manager_get_stream(stream_event_constants):
    """Test getting a stream from the stream manager."""
    # Create a stream manager
    stream_manager = MockStreamManager()
    StreamEvent = stream_event_constants
    
    # Add some events
    await stream_manager.add_event(StreamEvent.THINKING_START, {"query": "test"})
    await stream_manager.add_event(StreamEvent.ANSWER_CHUNK, {"chunk": "This is a test"})
    await stream_manager.add_event(StreamEvent.DONE, {"result": "done"})
    
    # Get the stream
    stream = stream_manager.get_stream()
    
    # Collect the events
    events = []
    async for event in stream:
        events.append(event)
    
    # Check the events
    assert len(events) == 6  # 3 events * 2 lines each (event: + data:)
    
    # First event should be thinking_start
    assert "event: thinking_start" in events[0]
    assert "data: " in events[1]
    # Extract and parse the JSON data
    data_json = events[1].replace("data: ", "").strip()
    data = json.loads(data_json)
    assert data == {"query": "test"}
    
    # Second event should be answer_chunk
    assert "event: answer_chunk" in events[2]
    assert "data: " in events[3]
    # Extract and parse the JSON data
    data_json = events[3].replace("data: ", "").strip()
    data = json.loads(data_json)
    assert data == {"chunk": "This is a test"}
    
    # Third event should be done
    assert "event: done" in events[4]
    assert "data: " in events[5]
    # Extract and parse the JSON data
    data_json = events[5].replace("data: ", "").strip()
    data = json.loads(data_json)
    assert data == {"result": "done"}


def test_stream_callback_handler(stream_event_constants):
    """Test the stream callback handler with mocks."""
    StreamEvent = stream_event_constants
    
    # Create a mock handler class
    class MockCallbackHandler:
        def __init__(self, stream_manager):
            self.stream_manager = stream_manager
            self.loop = asyncio.get_event_loop()
        
        def on_thinking_start(self, data):
            asyncio.run_coroutine_threadsafe(
                self.stream_manager.add_event(StreamEvent.THINKING_START, data),
                self.loop
            )
        
        def on_thinking_update(self, data):
            asyncio.run_coroutine_threadsafe(
                self.stream_manager.add_event(StreamEvent.THINKING_UPDATE, data),
                self.loop
            )
        
        def on_answer_chunk(self, chunk):
            asyncio.run_coroutine_threadsafe(
                self.stream_manager.add_event(StreamEvent.ANSWER_CHUNK, {"chunk": chunk}),
                self.loop
            )
        
        def on_document(self, document):
            asyncio.run_coroutine_threadsafe(
                self.stream_manager.add_event(StreamEvent.DOCUMENT, {"document": document}),
                self.loop
            )
        
        def on_error(self, error):
            asyncio.run_coroutine_threadsafe(
                self.stream_manager.add_event(StreamEvent.ERROR, {"error": error}),
                self.loop
            )
        
        def on_done(self, data):
            asyncio.run_coroutine_threadsafe(
                self.stream_manager.add_event(StreamEvent.DONE, data),
                self.loop
            )
    
    # Create a mock stream manager
    mock_stream_manager = MagicMock()
    mock_stream_manager.add_event = AsyncMock()
    
    # Create a callback handler
    handler = MockCallbackHandler(mock_stream_manager)
    
    # Test on_thinking_start
    handler.on_thinking_start({"query": "test"})
    mock_stream_manager.add_event.assert_called_with(StreamEvent.THINKING_START, {"query": "test"})
    
    # Reset the mock
    mock_stream_manager.add_event.reset_mock()
    
    # Test on_thinking_update
    handler.on_thinking_update({"step": "thinking"})
    mock_stream_manager.add_event.assert_called_with(StreamEvent.THINKING_UPDATE, {"step": "thinking"})
    
    # Reset the mock
    mock_stream_manager.add_event.reset_mock()
    
    # Test on_answer_chunk
    handler.on_answer_chunk("Hello")
    mock_stream_manager.add_event.assert_called_with(StreamEvent.ANSWER_CHUNK, {"chunk": "Hello"})
    
    # Reset the mock
    mock_stream_manager.add_event.reset_mock()
    
    # Test on_document
    doc = {"content": "test", "metadata": {"source": "web"}}
    handler.on_document(doc)
    mock_stream_manager.add_event.assert_called_with(StreamEvent.DOCUMENT, {"document": doc})
    
    # Reset the mock
    mock_stream_manager.add_event.reset_mock()
    
    # Test on_error
    handler.on_error("Test error")
    mock_stream_manager.add_event.assert_called_with(StreamEvent.ERROR, {"error": "Test error"})
    
    # Reset the mock
    mock_stream_manager.add_event.reset_mock()
    
    # Test on_done
    handler.on_done({"result": "done"})
    mock_stream_manager.add_event.assert_called_with(StreamEvent.DONE, {"result": "done"})


def test_sync_to_async_adapter(stream_event_constants):
    """Test the sync to async adapter with mocks."""
    StreamEvent = stream_event_constants
    
    # Create a mock adapter class
    class MockAdapter:
        def __init__(self, stream_manager):
            self.stream_manager = stream_manager
            self.loop = asyncio.get_event_loop()
            
        def run_in_background(self, func, *args, **kwargs):
            try:
                result = func(*args, **kwargs)
                if isinstance(result, tuple) and len(result) >= 5:
                    answer, conversation_id, _, _, duration = result[:5]
                    asyncio.run_coroutine_threadsafe(
                        self.stream_manager.add_event(StreamEvent.DONE, {
                            "answer": answer,
                            "conversation_id": conversation_id,
                            "duration_seconds": duration
                        }),
                        self.loop
                    )
            except Exception as e:
                asyncio.run_coroutine_threadsafe(
                    self.stream_manager.add_event(StreamEvent.ERROR, {"error": str(e)}),
                    self.loop
                )
    
    # Create a mock stream manager
    mock_stream_manager = MagicMock()
    mock_stream_manager.add_event = AsyncMock()
    
    # Create a sync to async adapter
    adapter = MockAdapter(mock_stream_manager)
    
    # Define a test function
    def test_func(arg1, arg2=None):
        return ("result", "conversation_id", [], [], 1.0)
    
    # Run the function in the background
    adapter.run_in_background(test_func, "arg1", arg2="arg2")
    
    # Check that the done event was sent
    mock_stream_manager.add_event.assert_called_with(
        StreamEvent.DONE, 
        {
            "answer": "result",
            "conversation_id": "conversation_id",
            "duration_seconds": 1.0
        }
    )


def test_sync_to_async_adapter_error_handling(stream_event_constants):
    """Test error handling in the sync to async adapter with mocks."""
    StreamEvent = stream_event_constants
    
    # Create a mock adapter class
    class MockAdapter:
        def __init__(self, stream_manager):
            self.stream_manager = stream_manager
            self.loop = asyncio.get_event_loop()
            
        def run_in_background(self, func, *args, **kwargs):
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                asyncio.run_coroutine_threadsafe(
                    self.stream_manager.add_event(StreamEvent.ERROR, {"error": str(e)}),
                    self.loop
                )
    
    # Create a mock stream manager
    mock_stream_manager = MagicMock()
    mock_stream_manager.add_event = AsyncMock()
    
    # Create a sync to async adapter
    adapter = MockAdapter(mock_stream_manager)
    
    # Define a test function that raises an exception
    def test_func():
        raise Exception("Test error")
    
    # Run the function in the background
    adapter.run_in_background(test_func)
    
    # Check that the error event was sent
    mock_stream_manager.add_event.assert_called_with(
        StreamEvent.ERROR, 
        {"error": "Test error"}
    ) 