import asyncio
import websockets
import json
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_websocket():
    # Test configuration
    user_id = "test-user-1"
    api_key = "test-key-123"
    uri = f"ws://localhost:8000/ws/{user_id}?x-api-key={api_key}"
    
    try:
        logger.info(f"Attempting to connect to {uri}")
        async with websockets.connect(uri) as websocket:
            logger.info("Successfully connected!")
            
            # Send a test message
            test_message = {
                "type": "test",
                "message": "Hello from test client!",
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send(json.dumps(test_message))
            logger.info(f"Sent message: {test_message}")
            
            # Wait for and process responses
            try:
                while True:
                    response = await websocket.recv()
                    logger.info(f"Received response: {response}")
                    
                    # Parse response
                    try:
                        response_data = json.loads(response)
                        if response_data.get("type") == "error":
                            logger.error(f"Received error: {response_data.get('error')}")
                    except json.JSONDecodeError:
                        logger.warning(f"Received non-JSON response: {response}")
                    
                    # Keep connection alive for a few seconds
                    await asyncio.sleep(2)
            except websockets.exceptions.ConnectionClosed:
                logger.info("Connection closed by server")
            
    except websockets.exceptions.InvalidStatusCode as e:
        logger.error(f"Failed to connect: {e}")
        if e.status_code == 403:
            logger.error("Authentication failed - check your API key")
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    logger.info("Starting WebSocket test...")
    asyncio.run(test_websocket()) 