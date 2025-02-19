import asyncio
import time

from constants import BLE_NAME, CHARACTERISTIC_UUID
from modules.ble_reader import BleReader
from modules.data_handler import DataHandler
from modules.sensor import Sensor



async def check(storage):
    while True:
        latest_data = storage.get_last_raw_data()
        if latest_data:
            print(f"📊 Processing data: {latest_data}")
        await asyncio.sleep(2)

async def main():
    sensor_1 = Sensor()
    sensor_2 = Sensor()
    data_handler = DataHandler(sensor_1, sensor_2)
    ble_reader = BleReader(BLE_NAME, CHARACTERISTIC_UUID, data_handler)

    ble_task = asyncio.create_task(ble_reader.connect_and_listen())
    process_task = asyncio.create_task(check(data_handler))

    await asyncio.gather(ble_task, process_task)

if __name__ == "__main__":
    asyncio.run(main())