"""
Streaming service for Kevin API.

This module provides utilities for handling streaming responses and callbacks.
"""

import json
import asyncio
import threading
import time
from typing import Dict, Any, List, Optional, Callable, AsyncGenerator
from queue import Queue
from concurrent.futures import ThreadPoolExecutor

from src.utils.logger import get_logger

logger = get_logger(__name__)


class StreamEvent:
    """Stream event types for Server-Sent Events (SSE)."""
    
    THINKING_START = "thinking_start"
    THINKING_UPDATE = "thinking_update"
    THINKING_END = "thinking_end"
    ANSWER = "answer"
    ANSWER_START = "answer_start"
    ANSWER_CHUNK = "answer_chunk"
    ANSWER_END = "answer_end"
    DOCUMENT = "document"
    DOCUMENTS = "documents"
    ERROR = "error"
    DONE = "done"
    CACHED = "cached"


class StreamManager:
    """
    Manages a streaming response queue for Server-Sent Events (SSE).
    
    This class handles the queue of events to be sent to the client,
    and provides a generator to yield SSE-formatted events.
    """
    
    def __init__(self):
        """Initialize a new stream manager."""
        self.queue = asyncio.Queue()
        self.is_done = False
        
    async def add_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Add an event to the stream queue.
        
        Args:
            event_type: The type of event (see StreamEvent class).
            data: The data to include in the event.
        """
        await self.queue.put((event_type, data))
        
        # If this is a DONE or ERROR event, mark the stream as done
        if event_type in [StreamEvent.DONE, StreamEvent.ERROR]:
            self.is_done = True
    
    async def get_stream(self) -> AsyncGenerator[str, None]:
        """
        Get a generator that yields SSE-formatted events.
        
        Returns:
            An async generator that yields SSE-formatted events.
        """
        while not (self.is_done and self.queue.empty()):
            try:
                # Wait for an event with a timeout
                event_type, data = await asyncio.wait_for(self.queue.get(), timeout=60.0)
                
                # Format as SSE
                yield f"event: {event_type}\n"
                yield f"data: {json.dumps(data)}\n\n"
                
                # Mark as done
                self.queue.task_done()
                
                # If this is a DONE or ERROR event, break after sending
                if event_type in [StreamEvent.DONE, StreamEvent.ERROR]:
                    break
                    
            except asyncio.TimeoutError:
                # Send a keepalive comment after timeout
                yield ": keepalive\n\n"
            except Exception as e:
                logger.error(f"Error in stream generator: {e}")
                # Send an error event
                error_data = {"error": str(e)}
                yield f"event: {StreamEvent.ERROR}\n"
                yield f"data: {json.dumps(error_data)}\n\n"
                break


class StreamCallbackHandler:
    """
    Callback handler for streaming responses.
    
    This class provides callback methods that can be passed to the
    agent or other components to receive updates and stream them to the client.
    """
    
    def __init__(self, stream_manager: StreamManager):
        """
        Initialize a new stream callback handler.
        
        Args:
            stream_manager: The stream manager to add events to.
        """
        self.stream_manager = stream_manager
        self.loop = asyncio.get_event_loop()
        
    def on_thinking_start(self, data: Dict[str, Any]) -> None:
        """Called when thinking starts."""
        asyncio.run_coroutine_threadsafe(
            self.stream_manager.add_event(StreamEvent.THINKING_START, data),
            self.loop
        )
        
    def on_thinking_update(self, data: Dict[str, Any]) -> None:
        """Called when thinking is updated."""
        asyncio.run_coroutine_threadsafe(
            self.stream_manager.add_event(StreamEvent.THINKING_UPDATE, data),
            self.loop
        )
        
    def on_thinking_end(self, data: Dict[str, Any]) -> None:
        """Called when thinking ends."""
        asyncio.run_coroutine_threadsafe(
            self.stream_manager.add_event(StreamEvent.THINKING_END, data),
            self.loop
        )
        
    def on_answer_start(self) -> None:
        """Called when the answer starts."""
        asyncio.run_coroutine_threadsafe(
            self.stream_manager.add_event(StreamEvent.ANSWER_START, {}),
            self.loop
        )
        
    def on_answer_chunk(self, chunk: str) -> None:
        """Called for each chunk of the answer."""
        asyncio.run_coroutine_threadsafe(
            self.stream_manager.add_event(StreamEvent.ANSWER_CHUNK, {"chunk": chunk}),
            self.loop
        )
        
    def on_answer_end(self) -> None:
        """Called when the answer ends."""
        asyncio.run_coroutine_threadsafe(
            self.stream_manager.add_event(StreamEvent.ANSWER_END, {}),
            self.loop
        )
    
    def on_answer(self, answer: str) -> None:
        """Called when a complete answer is available (e.g., from cache)."""
        asyncio.run_coroutine_threadsafe(
            self.stream_manager.add_event(StreamEvent.ANSWER, {"answer": answer}),
            self.loop
        )
        
    def on_document(self, document: Dict[str, Any]) -> None:
        """Called when a document is available."""
        asyncio.run_coroutine_threadsafe(
            self.stream_manager.add_event(StreamEvent.DOCUMENT, {"document": document}),
            self.loop
        )
    
    def on_documents(self, documents: List[Dict[str, Any]]) -> None:
        """Called when multiple documents are available at once."""
        asyncio.run_coroutine_threadsafe(
            self.stream_manager.add_event(StreamEvent.DOCUMENTS, {"documents": documents}),
            self.loop
        )
        
    def on_error(self, error: str) -> None:
        """Called when an error occurs."""
        asyncio.run_coroutine_threadsafe(
            self.stream_manager.add_event(StreamEvent.ERROR, {"error": error}),
            self.loop
        )
        
    def on_complete(self) -> None:
        """Called when the response is complete."""
        asyncio.run_coroutine_threadsafe(
            self.stream_manager.add_event(StreamEvent.DONE, {}),
            self.loop
        )


class SyncToAsyncAdapter:
    """
    Adapter for running synchronous functions in a background thread.
    
    This class provides utilities for running synchronous functions
    in a background thread and communicating with the async world.
    """
    
    def __init__(self, stream_manager: StreamManager):
        """
        Initialize a new sync-to-async adapter.
        
        Args:
            stream_manager: The stream manager to add events to.
        """
        self.stream_manager = stream_manager
        self.loop = asyncio.get_event_loop()
        self.executor = ThreadPoolExecutor(max_workers=1)
        
    def run_in_background(self, func: Callable, *args, **kwargs) -> None:
        """
        Run a synchronous function in a background thread.
        
        Args:
            func: The function to run.
            *args: Positional arguments to pass to the function.
            **kwargs: Keyword arguments to pass to the function.
        """
        self.executor.submit(self._run_and_handle_exceptions, func, *args, **kwargs)
        
    def _run_and_handle_exceptions(self, func: Callable, *args, **kwargs) -> None:
        """
        Run a function and handle any exceptions.
        
        Args:
            func: The function to run.
            *args: Positional arguments to pass to the function.
            **kwargs: Keyword arguments to pass to the function.
        """
        try:
            # Run the function
            func(*args, **kwargs)
            
            # Note: We don't need to add a DONE event here anymore,
            # as it's now handled by the callback handler in process_chat
            
        except Exception as e:
            logger.error(f"Error in background task: {e}", exc_info=True)
            # Send an ERROR event
            asyncio.run_coroutine_threadsafe(
                self.stream_manager.add_event(StreamEvent.ERROR, {"error": str(e)}),
                self.loop
            ) 