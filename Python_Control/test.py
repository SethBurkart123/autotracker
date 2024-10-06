import asyncio
import websockets

async def test_client():
    uri = "ws://localhost:9000"
    async with websockets.connect(uri) as websocket:
        await websocket.send('{"command": "subscribe"}')
        while True:
            message = await websocket.recv()
            print("Received:", message)

# Replace the last line with:
asyncio.run(test_client())