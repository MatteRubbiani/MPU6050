import asyncio
import redis
import websockets

from constants import CHANNEL


async def send_data(_pubsub):
    """
    Connect to a WebSocket server and send data.
    """
    websocket_url = "ws://localhost:8765"  # Replace with your WebSocket server URL
    try:
        async with websockets.connect(websocket_url) as websocket:
            # Continuously listen for new messages
            for message in _pubsub.listen():
                # Message type 'message' means it is a published message
                if message['type'] == 'message':
                    data = message['data'].decode('utf-8')
                    if websocket is not None:
                        await websocket.send(data)
                        print(f"Sent: {data}")
                    else:
                        print("Failed to connect to websocket")
    except Exception as e:
        print(f"Error: {e}")


# Run the WebSocket client
if __name__ == "__main__":
    r = redis.Redis(host='localhost', port=6379, db=0)

    # Create a Pub/Sub object to listen to the channel
    pubsub = r.pubsub()
    print(pubsub)
    pubsub.subscribe(CHANNEL)
    asyncio.run(send_data(pubsub))
