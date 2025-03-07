import asyncio
import time

from constants import BLE_NAME, CHARACTERISTIC_UUID
from modules.ble_reader import BleReader
from modules.data_handler_v2 import DataHandler
from modules.leg import Leg
from modules.sensor import Sensor
from streaming.socket_streaming import SocketStreaming


async def check(storage):
    while True:
        latest_data = storage.get_last_raw_data()
        if latest_data:
            print(f"📊 Processing data: {latest_data}")
        await asyncio.sleep(2)

async def main():
    sensor_1 = Sensor()
    sensor_2 = Sensor()
    data_handler = DataHandler(sensor_1, sensor_2, CHARACTERISTIC_UUID, "nop")
    leg = Leg(sensor_1, sensor_2)

    ble_reader = BleReader(BLE_NAME, CHARACTERISTIC_UUID, data_handler)
    streamer = SocketStreaming(leg)

    ble_task = asyncio.create_task(ble_reader.connect_and_listen())
    # process_task = asyncio.create_task(check(data_handler))
    streaming_task = asyncio.create_task(streamer.start_server())

    await asyncio.gather(ble_task, streaming_task)

if __name__ == "__main__":
    asyncio.run(main())