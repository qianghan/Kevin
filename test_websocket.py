#!/usr/bin/env python
"""Test WebSocket connection to profiler backend."""

import asyncio
import websockets
import json
import logging
import sys

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("websocket_test")

async def test_websocket():
    """Test the WebSocket connection with detailed logging."""
    uri = "ws://localhost:8000/ws/test-user?x-api-key=test-key-123"
    
    logger.info(f"Connecting to {uri}")
    async with websockets.connect(uri) as websocket:
        logger.info("Connected to WebSocket")
        
        # Receive the welcome message
        message = await websocket.recv()
        logger.info(f"Received welcome message: {message}")
        
        # Receive the connected message from connection manager
        response = await websocket.recv()
        logger.info(f"Received connection message: {response}")
        
        # Test different sections to see if they work
        sections = ["academic", "personal", "extracurricular", "essays"]
        
        for section in sections:
            # Send a switch_section message
            test_message = json.dumps({
                "type": "switch_section",
                "data": {
                    "section": section,
                    "timestamp": "2023-04-16T12:00:00Z"
                }
            })
            logger.info(f"Sending switch_section message for section '{section}'")
            await websocket.send(test_message)
            
            # Receive response to switch_section
            response = await websocket.recv()
            logger.info(f"Received response for section '{section}': {response}")
            
            # Wait a bit between sections
            await asyncio.sleep(0.5)
        
        # Test with an echo message to verify basic message handling
        echo_message = json.dumps({"type": "echo", "message": "This is an echo test"})
        logger.info(f"Sending echo message")
        await websocket.send(echo_message)
        
        # Receive echo response
        try:
            response = await websocket.recv()
            logger.info(f"Received echo response: {response}")
        except Exception as e:
            logger.error(f"Error receiving echo response: {e}")
        
        # Wait a bit before closing
        await asyncio.sleep(1)
        logger.info("Test completed successfully")

if __name__ == "__main__":
    asyncio.run(test_websocket()) 