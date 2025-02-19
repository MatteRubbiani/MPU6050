import time

from data_processing_v3 import parse_data_v3


class DataHandler:
    def __init__(self, sensor_1, sensor_2):
        self.sensor_1 = sensor_1
        self.sensor_2 = sensor_2

        self.raw_readings = []
        self.start_time = time.time()

    def add_data(self, new_data):
        self.raw_readings.append(new_data)
        parsed_data = parse_data_v3(new_data)
        data_type = parsed_data["data_type"]
        if data_type == "*-":
            self.sensor_1.add_gravity_recording(parsed_data["g"])
            self.sensor_1.calculate_and_set_starting_quaternion()
        elif data_type == "**":
            self.sensor_1.add_gravity_recording(parsed_data["g_68"])
            self.sensor_1.calculate_and_set_starting_quaternion()
            self.sensor_2.add_gravity_recording(parsed_data["g_69"])
            self.sensor_2.calculate_and_set_starting_quaternion()
        elif data_type == "#-":
            self.sensor_1.add_recording(parsed_data["timestamp"], parsed_data["quaternion"], parsed_data["acceleration"])
            self.sensor_1.calculate_and_set_state()
        elif data_type == "##":
            self.sensor_1.add_recording(parsed_data["timestamp"], parsed_data["quaternion_68"], parsed_data["acceleration_68"])
            self.sensor_1.calculate_and_set_state()
            self.sensor_2.add_recording(parsed_data["timestamp"], parsed_data["quaternion_69"], parsed_data["acceleration_69"])
            self.sensor_2.calculate_and_set_state()

    def save_data_to_file(self):
        #todo: handle saving data
        pass

    # boh non so se lo uso
    def clear_data(self, new_sensor_1, new_sensor_2):
        self.raw_readings = []
        self.sensor_1 = new_sensor_1
        self.sensor_2 = new_sensor_2

    def get_last_raw_data(self):
        if len(self.raw_readings) > 0:
            return self.raw_readings[-1]