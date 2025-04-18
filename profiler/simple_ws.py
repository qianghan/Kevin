import asyncio, websockets, json
async def main():
    uri = "ws://localhost:8000/ws/test-user-1?x-api-key=test-key-123"
    print(f"Connecting to {uri}")
    async with websockets.connect(uri) as ws:
        print("Connected")
        msg1 = await ws.recv()
        print(f"Received 1: {msg1}")
        msg2 = await ws.recv()
        print(f"Received 2: {msg2}")
        switch_msg = json.dumps({"type": "switch_section", "data": {"section": "personal"}})
        print(f"Sending: {switch_msg}")
        await ws.send(switch_msg)
        resp = await ws.recv()
        print(f"Response: {resp}")
        data = json.loads(resp)
        if data.get("data", {}).get("current_section") == "personal":
            print("SUCCESS: Section switched")
        else:
            print("FAILED: Section not switched")
asyncio.run(main())
