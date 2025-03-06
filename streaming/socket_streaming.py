import asyncio
import json

import websockets
import logging

from constants import PYTHON_SAMPLING_RATE
from modules.leg import Leg
from modules.sensor import Sensor

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class SocketStreaming:
    def __init__(self, leg:Leg, host="localhost", port=8765, retry_delay=5):
        self.leg = leg

        self.host = host
        self.port = port
        self.retry_delay = retry_delay
        self.clients = set()
        self.server = None

    async def handler(self, websocket):
        """Handles new WebSocket connections."""
        logging.info(f"New connection from {websocket.remote_address}")
        self.clients.add(websocket)
        try:
            while True:
                #todo: ovviamente sistemare
                data = self.leg.get_sensor_pose()
                await websocket.send(json.dumps(data))

                await asyncio.sleep(PYTHON_SAMPLING_RATE)

        except websockets.exceptions.ConnectionClosed:
            logging.warning(f"Connection closed: {websocket.remote_address}")
        finally:
            self.clients.remove(websocket)

    async def start_server(self):
        """Starts the WebSocket server with automatic recovery."""
        while True:
            try:
                async with websockets.serve(self.handler, self.host, self.port):
                    logging.info(f"WebSocket server running on ws://{self.host}:{self.port}")
                    await asyncio.Future()  # Keep the server running
            except Exception as e:
                logging.error(f"WebSocket server error: {e}")
                logging.info(f"Restarting server in {self.retry_delay} seconds...")
                await asyncio.sleep(self.retry_delay)

if __name__ == "__main__":
    sensor_1 = Sensor()
    sensor_2 = Sensor()
    server = SocketStreaming(Leg(sensor_1, sensor_2))
    asyncio.run(server.start_server())
