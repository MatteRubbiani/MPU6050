import asyncio
from bleak import BleakClient, BleakScanner, BleakError

from modules.data_handler_v2 import DataHandler


class BleReader:
    def __init__(self, device_name: str, characteristic_uuid_notify: str, data_handler: DataHandler, characteristic_uuid_command):
        self.device_name = device_name
        self.characteristic_uuid_notify = characteristic_uuid_notify
        self.characteristic_uuid_command = characteristic_uuid_command
        self.client = None
        self.address = None

        self.data_handler = data_handler

    async def _find_device(self):
        """Scan for the ESP32 device and return its address."""
        print("Scanning for ESP32...")
        devices = await BleakScanner.discover()

        for device in devices:
            if device.name and self.device_name in device.name:
                print(f"Found device: {device.name} ({device.address})")
                return device.address
        print("ESP32 not found. Make sure it's advertising.")
        return None

    async def _notification_handler(self, sender: int, data: bytes):
        """Callback when a notification is received."""
        try:
            decoded_data = data.decode("utf-8")
            self.data_handler.add_data(decoded_data, self.characteristic_uuid_notify)
            print(f"🔔 Received from {sender}: {decoded_data}")
        except Exception as e:
            print(f"❌ Error decoding: {e}, Raw data: {data}")



    async def connect_and_listen(self):
        """Scan for ESP32, connect, and listen for notifications, with automatic reconnection."""
        while True:
            if not self.address:
                self.address = await self._find_device()
                if not self.address:
                    await asyncio.sleep(5)
                    continue

            try:
                self.client = BleakClient(self.address, timeout=10)
                await self.client.connect()
                print("Connected! Waiting for services...")
                await asyncio.sleep(2)

                services = await self.client.get_services()
                characteristic_uuids = [char.uuid for service in services for char in service.characteristics]

                if self.characteristic_uuid_notify not in characteristic_uuids:
                    print("Characteristic UUID not found. Check your ESP32 code.")
                    await self.client.disconnect()
                    self.address = None
                    continue

                await self.client.start_notify(self.characteristic_uuid_notify, self._notification_handler)
                print("Listening for notifications.")

                while True:
                    if not self.client.is_connected:
                        raise BleakError("Disconnected from device")
                    await asyncio.sleep(1)
            except (asyncio.CancelledError, KeyboardInterrupt):
                print("Stopping notifications...")
                if self.client:
                    await self.client.stop_notify(self.characteristic_uuid_notify)
                    await self.client.disconnect()
                break
            except BleakError as e:
                print(f"⚠️ Connection lost: {e}. Reconnecting...")
                self.address = None
                await asyncio.sleep(5)
            except Exception as e:
                print(f"⚠️ Unexpected error: {e}. Reconnecting...")
                await asyncio.sleep(5)

        print("Disconnected.")

    # provo ad aggiungere
    async def send_data(self, message: str):
        """Send data to the ESP32 over BLE."""
        if self.client and self.client.is_connected:
            try:
                await self.client.write_gatt_char(self.characteristic_uuid_command, message.encode("utf-8"), response=True)
                print(f"📤 Sent: {message}")
            except Exception as e:
                print(f"❌ Failed to send: {e}")
        else:
            print("⚠️ Not connected. Cannot send data.")


async def main():
    ESP32_NAME = "Long name works now"  # Change to match your ESP32 device name
    CHARACTERISTIC_UUID_NOTIFY = "beb5483e-36e1-4688-b7f5-ea07361b26a8"  # Must match ESP32 code
    CHARACTERISTIC_UUID_COMMAND = "beb5483e-36e1-4688-b7f5-ea07361b26a9"
    from modules.sensor import Sensor
    sensor_1 = Sensor()
    sensor_2 = Sensor()
    data_handler = DataHandler(sensor_1, sensor_2, CHARACTERISTIC_UUID_NOTIFY, "nop")
    ble_reader = BleReader(ESP32_NAME, CHARACTERISTIC_UUID_NOTIFY, data_handler, CHARACTERISTIC_UUID_COMMAND)



    async def user_input_loop(b_r):
        async def async_input(prompt: str) -> str:
            """Get user input asynchronously without blocking."""
            return await asyncio.to_thread(input, prompt)
        while True:
            message = await async_input("📩 Enter message: ")
            await b_r.send_data(message)
    input_task = asyncio.create_task(user_input_loop(ble_reader))
    logging_task = asyncio.create_task(ble_reader.connect_and_listen())

    await asyncio.gather(logging_task, input_task)
    asyncio.run(ble_reader.connect_and_listen())

if __name__ == "__main__":
    asyncio.run(main())