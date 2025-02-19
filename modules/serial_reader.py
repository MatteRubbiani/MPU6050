import json

import numpy as np
import redis
import serial
import serial.tools.list_ports
import threading
import time
import logging

from constants import CHANNEL
from colorama import Fore, Style

from data_processing_v3 import parse_data_v3
from sensor import Sensor

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")

#todo: implementare DataHandler anche qua
class SerialReader:
    def __init__(self, port="/dev/tty.usbserial-0001", baudrate=115200, timeout=1, reconnect=True, r:redis.Redis=None):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.reconnect = reconnect
        self.serial_connection = None
        self.running = False
        self.thread = None
        self.r = r
        self.sensor_1 = Sensor(initial_position=np.array([0, 0, 0]))
        self.sensor_2 = Sensor(initial_position=np.array([0, 3, 3]))

    def find_device(self):
        """Automatically detects an available serial device if no port is specified."""
        if self.port:
            return self.port
        # NON LO USO IN MODALITà AUTOMATICA MA LO LASCIO
        ports = serial.tools.list_ports.comports()
        if not ports:
            logging.warning("No serial devices found.")
            return None

        # Automatically select the first detected port
        detected_port = ports[0].device
        logging.info(f"Auto-detected device on: {detected_port}")
        return detected_port

    def connect(self):
        """Establishes a connection to the serial device."""
        self.port = self.find_device()
        if not self.port:
            return

        try:
            self.serial_connection = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            time.sleep(2)  # Allow the Arduino to reset
            logging.info(f"Connected to {self.port} at {self.baudrate} baud.")
        except serial.SerialException as e:
            logging.error(f"Failed to connect to {self.port}: {e}")
            self.serial_connection = None

    def read_serial_data(self):
        """Reads data from the serial port with error handling."""
        try:
            if self.serial_connection and self.serial_connection.in_waiting > 0:
                data = self.serial_connection.readline().decode('utf-8', errors='ignore').strip()
                return data if data else None
        except (serial.SerialException, OSError) as e:
            logging.error(f"Serial error: {e}")
            self.serial_connection = None  # Mark connection as lost
        return None

    def read_loop(self):
        """Continuously reads from serial in a separate thread."""
        while self.running:
            if self.serial_connection is None and self.reconnect:
                logging.info("Attempting to reconnect...")
                self.connect()

            raw_data = self.read_serial_data()
            if raw_data:
                self.process_data(raw_data)

            time.sleep(0.05)  # Adjust polling rate as needed

    def process_data(self, data):
        logging.info(f"Processing data: {data}")
        parsed_data = parse_data_v3(data)
        data_type = parsed_data["data_type"]
        data_to_send_sensor_1 = None
        data_to_send_sensor_2 = None
        if data_type == "*-":
            self.sensor_1.add_gravity_recording(parsed_data["g"])
            self.sensor_1.calculate_and_set_starting_quaternion()
            data_to_send_sensor_1 = self.sensor_1.get_pose("*")
        elif data_type == "**":
            self.sensor_1.add_gravity_recording(parsed_data["g_68"])
            self.sensor_1.calculate_and_set_starting_quaternion()
            self.sensor_2.add_gravity_recording(parsed_data["g_69"])
            self.sensor_2.calculate_and_set_starting_quaternion()
            data_to_send_sensor_1 = self.sensor_1.get_pose("*")
            data_to_send_sensor_2 = self.sensor_2.get_pose("*")
        elif data_type == "#-":
            self.sensor_1.add_recording(parsed_data["timestamp"], parsed_data["quaternion"], parsed_data["acceleration"])
            self.sensor_1.calculate_and_set_state()
            data_to_send_sensor_1 = self.sensor_1.get_pose("#")
        elif data_type == "##":
            self.sensor_1.add_recording(parsed_data["timestamp"], parsed_data["quaternion_68"], parsed_data["acceleration_68"])
            self.sensor_1.calculate_and_set_state()
            self.sensor_2.add_recording(parsed_data["timestamp"], parsed_data["quaternion_69"], parsed_data["acceleration_69"])
            self.sensor_2.calculate_and_set_state()
            data_to_send_sensor_1 = self.sensor_1.get_pose("#")
            data_to_send_sensor_2 = self.sensor_2.get_pose("#")
        else:
            logging.error(f"Unknown data type: {data_type}")

        data_to_publish = {
            "sensor_1" : data_to_send_sensor_1,
            "sensor_2" : data_to_send_sensor_2,
        }
        self.publish_data_to_redis(data_to_publish)

    def publish_data_to_redis(self, data):
        """Publish received data to redis."""
        if self.r:
            # logging.info(Fore.GREEN + f"Publishing data to redis! {data}" + Style.RESET_ALL)
            self.r.publish(CHANNEL, json.dumps(data))

    def start(self):
        """Starts the serial reading thread."""
        self.running = True
        self.thread = threading.Thread(target=self.read_loop, daemon=True)
        self.thread.start()
        logging.info("Serial reading thread started.")

    def stop(self):
        """Stops the serial reader and closes the connection."""
        self.running = False
        if self.thread:
            self.thread.join()
        if self.serial_connection:
            self.serial_connection.close()
            logging.info("Serial connection closed.")


if __name__ == "__main__":
    reader = SerialReader(baudrate=115200)
    reader.start()

    try:
        while True:
            time.sleep(1)  # Keep main thread alive
    except KeyboardInterrupt:
        logging.info("Stopping...")
        reader.stop()
