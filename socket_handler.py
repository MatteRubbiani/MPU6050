import asyncio
import websockets

# Set to keep track of all connected clients
connected_clients = set()

async def handler(websocket):
    # Register the new client connection
    connected_clients.add(websocket)
    try:
        # Listen for incoming messages from this specific client
        async for message in websocket:
            # Broadcast the received message to all connected clients
            await broadcast(message)
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        # Remove client from the set when they disconnect
        connected_clients.remove(websocket)

# Function to broadcast messages to all connected clients
async def broadcast(message):
    # Send the message to all connected clients
    for client in connected_clients:
        try:
            await client.send(message)
        except websockets.exceptions.ConnectionClosed:
            # Ignore disconnected clients
            connected_clients.remove(client)

# Start the WebSocket server
async def start_server():
    server = await websockets.serve(handler, "localhost", 8765)
    await server.wait_closed()

# Run the WebSocket server
asyncio.get_event_loop().run_until_complete(start_server())
