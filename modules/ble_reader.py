import asyncio
from bleak import BleakClient, BleakScanner, BleakError

from modules.data_handler import DataHandler


class BleReader:
    def __init__(self, device_name: str, characteristic_uuid: str, data_handler: DataHandler):
        self.device_name = device_name
        self.characteristic_uuid = characteristic_uuid
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
            self.data_handler.add_data(decoded_data)
            # print(f"🔔 Received from {sender}: {decoded_data}")
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

                if self.characteristic_uuid not in characteristic_uuids:
                    print("Characteristic UUID not found. Check your ESP32 code.")
                    await self.client.disconnect()
                    self.address = None
                    continue

                await self.client.start_notify(self.characteristic_uuid, self._notification_handler)
                print("Listening for notifications. Press Ctrl+C to stop.")

                while True:
                    if not self.client.is_connected:
                        raise BleakError("Disconnected from device")
                    await asyncio.sleep(1)
            except (asyncio.CancelledError, KeyboardInterrupt):
                print("Stopping notifications...")
                if self.client:
                    await self.client.stop_notify(self.characteristic_uuid)
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


if __name__ == "__main__":
    ESP32_NAME = "Long name works now"  # Change to match your ESP32 device name
    CHARACTERISTIC_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"  # Must match ESP32 code
    data_handler = DataHandler(1, 2)
    ble_reader = BleReader(ESP32_NAME, CHARACTERISTIC_UUID, data_handler)
    asyncio.run(ble_reader.connect_and_listen())
