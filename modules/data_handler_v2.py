import time

from data_processing_v4 import parse_data_v4


class DataHandler:
    def __init__(self, sensor_1, sensor_2, characteristic_uuid_sensor_1, characteristic_uuid_sensor_2):
        self.sensors = {
            characteristic_uuid_sensor_1: sensor_1,
            characteristic_uuid_sensor_2: sensor_2,
        }

        self.raw_readings = []
        self.start_time = time.time()

    def add_data(self, new_data, c_uuid):
        self.raw_readings.append(new_data)
        parsed_data = parse_data_v4(new_data)
        data_type = parsed_data["data_type"]
        sensor = self.sensors[c_uuid]
        if data_type == "*":
            sensor.add_gravity_recording(parsed_data["g"])
            sensor.calculate_and_set_starting_quaternion()
        elif data_type == "#":
            sensor.add_recording(parsed_data["timestamp"], parsed_data["quaternion"], parsed_data["acceleration"])
            sensor.calculate_and_set_state()

    def save_data_to_file(self):
        #todo: handle saving data
        pass

    # boh non so se lo uso
    def clear_data(self, new_sensor_1, new_sensor_2):
        self.raw_readings = []
        self.sensors[0] = new_sensor_1
        self.sensors[1] = new_sensor_2

    def get_last_raw_data(self):
        if len(self.raw_readings) > 0:
            return self.raw_readings[-1]