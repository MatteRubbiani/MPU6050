import json
import math
import time

import numpy as np

from constants import CHANNEL, PYTHON_SIMULATION_SAMPLING_RATE
from data_processing_v3 import parse_data_v3
from sensor import Sensor


def simulate_main(r):

    time.sleep(1)
    sensor_1 = Sensor(filter_type="NONE", initial_position=np.array([0, 0, 0]))
    sensor_2 = Sensor(filter_type="NONE", initial_position=np.array([0, 3, 0]))
    SIMULATED_RECORDINGS_G = ["**,0,0,1,1,0,1" for i in range(10)]
    SIMULATED_RECORDINGS_POSES = [f"##,{i},1,{math.cos(i/10)},0,0,0,0,0,1,0,{math.cos(i/10)},0,0,0,0" for i in range(100)]
    SIMULATED_RECORDINGS = SIMULATED_RECORDINGS_G + SIMULATED_RECORDINGS_POSES

    for i in SIMULATED_RECORDINGS:
        print(f"SIMULATED RECORDING: {i}")
        parsed_data = parse_data_v3(i)
        data_type = parsed_data["data_type"]
        data_to_send_sensor_1 = None
        data_to_send_sensor_2 = None
        if data_type == "*-":
            sensor_1.add_gravity_recording(parsed_data["g"])
            sensor_1.calculate_and_set_starting_quaternion()
            data_to_send_sensor_1 = sensor_1.get_pose("*")
        elif data_type == "**":
            sensor_1.add_gravity_recording(parsed_data["g_68"])
            sensor_1.calculate_and_set_starting_quaternion()
            sensor_2.add_gravity_recording(parsed_data["g_69"])
            sensor_2.calculate_and_set_starting_quaternion()
            data_to_send_sensor_1 = sensor_1.get_pose("*")
            data_to_send_sensor_2 = sensor_2.get_pose("*")
        elif data_type == "#-":
            sensor_1.add_recording(parsed_data["timestamp"], parsed_data["quaternion_68"],
                                        parsed_data["acceleration_68"])
            sensor_1.calculate_and_set_state()
            data_to_send_sensor_1 = sensor_1.get_pose("#")
        elif data_type == "##":
            sensor_1.add_recording(parsed_data["timestamp"], parsed_data["quaternion_68"],
                                        parsed_data["acceleration_68"])
            sensor_1.calculate_and_set_state()
            sensor_2.add_recording(parsed_data["timestamp"], parsed_data["quaternion_69"],
                                        parsed_data["acceleration_69"])
            sensor_2.calculate_and_set_state()
            data_to_send_sensor_1 = sensor_1.get_pose("#")
            data_to_send_sensor_2 = sensor_2.get_pose("#")
        data_to_send = {
            "sensor_1": data_to_send_sensor_1,
            "sensor_2": data_to_send_sensor_2,
        }
        print("data_to_send:", data_to_send)

        r.publish(CHANNEL, json.dumps(data_to_send))
        time.sleep(PYTHON_SIMULATION_SAMPLING_RATE* 3)