import asyncio

import redis
import websockets

from constants import CHANNEL, SOCKET_HOST, SOCKET_PORT

WEBSOCKET_URL = "ws://" + SOCKET_HOST + ":" + str(SOCKET_PORT)


async def send_data(_pubsub):
    """
    Connect to a WebSocket server and send data.
    """
    while True:
        try:
            async with websockets.connect(WEBSOCKET_URL, ping_interval=30, close_timeout=100) as websocket:
                print("Connected to WebSocket server")
                # Continuously listen for new messages
                for message in _pubsub.listen():
                    # Message type 'message' means it is a published message
                    if message['type'] == 'message':
                        data = message['data'].decode('utf-8')
                        if websocket is not None:
                            try:
                                await websocket.send(data)
                            except websockets.exceptions.ConnectionClosedError:
                                print("connection closed")
                                break
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
