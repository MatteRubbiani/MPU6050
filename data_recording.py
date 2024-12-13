import json
import os
import threading
import time
from collections import deque
from datetime import datetime, timezone

STANDARD_FILE_JSON = {
    "start_timestamp": time.time(),
    "exercise_code": "FL01",
    "calibration_code": "A",
    "calibration_duration": 10000,
    "g_static_components_at_rest": [0, 0, 9.81],
    "sampling_rate": 8,
    "starting_vector_tibia": [0, 0, 1],
    "starting_vector_femur": [0, 0, 1],
    "recording": [
        ["timestamp", "tibia quat", "femur quat"]]
}


def _generate_filename(base_name="rec", extension="json", use_utc=False, folder="recordings"):
    now = datetime.now(timezone.utc) if use_utc else datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{base_name}_{timestamp}.{extension}"

    # If folder is specified, combine it with the filename
    if folder:
        # Create the folder if it doesn't exist
        os.makedirs(folder, exist_ok=True)
        return os.path.join(folder, filename)
    return filename


class DataSaver:
    def __init__(self, exercise_code=None, calibration_code=None, calibration_duration=None, g_static=None,
                 sampling_rate=None, starting_vector_tibia=None, starting_vector_femur=None, buffer_size=1000):
        self.file_path = _generate_filename()
        self.exercise_code = exercise_code
        self.calibration_code = calibration_code
        self.calibration_duration = calibration_duration
        self.g_static = g_static
        self.sampling_rate = sampling_rate
        self.starting_vector_tibia = starting_vector_tibia
        self.starting_vector_femur = starting_vector_femur

        self.buffer_size = buffer_size
        self.data_buffer = deque(maxlen=self.buffer_size)

        self.buffer_size_counter = 0



    def _create_new_data(self):
        return {
            "start_timestamp": time.time(),
            "exercise_code": self.exercise_code,
            "calibration_code": self.calibration_code,
            "calibration_duration": self.calibration_duration,
            "g_static_components_at_rest": self.g_static,
            "sampling_rate": self.sampling_rate,
            "starting_vector_tibia": self.starting_vector_tibia,
            "starting_vector_femur": self.starting_vector_femur,
            "recordings": []
        }

    def _write_to_file(self):
        """Write the data buffer to the JSON file."""
        if not self.data_buffer:
            return

        # Lock the file operation to avoid race conditions
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, 'r') as f:
                    data = json.load(f)

            else:
                data = self._create_new_data()
            # Append the new data from the buffer
            data["recordings"].extend(self.data_buffer)
            with open(self.file_path, 'w') as f:
                json.dump(data, f, indent=4)
            # Clear the buffer after writing
            self.data_buffer.clear()
        except Exception as e:
            print(f"Error writing to file: {e}")

    def add_data(self, timestamp, tibia_quaternion, femur_quaternion):
        """
        Add a new data point to the buffer.

        :param femur_quaternion:
        :param timestamp:
        :param tibia_quaternion:
        """
        data_point = [timestamp, ] + tibia_quaternion + femur_quaternion
        self.data_buffer.append(data_point)
        self.buffer_size_counter += 1
        if self.buffer_size_counter == self.buffer_size:
            self._write_to_file()
            self.buffer_size_counter = 0


# Simulating the data input process
def simulate_data_input(data_saver, interval_ms=8):
    """
    Simulate incoming data every 8ms.

    :param data_saver: The DataSaver instance.
    :param interval_ms: Time interval in milliseconds to simulate incoming data.
    """
    while True:
        # Simulate incoming data (replace with actual data collection logic)
        data_point = {"timestamp": time.time(), "value": time.time() * 1000}
        data_saver.add_data(data_point)
        time.sleep(interval_ms / 1000.0)  # Convert ms to seconds
