import json
import time

import numpy as np
import redis
import serial

from constants import CHANNEL, ARDUINO_PORT, BAUD_RATE, REDIS_PORT,PYTHON_SIMULATION_SAMPLING_RATE
from data_processing_v2 import parse_data_one_sensor, parse_data_two_sensors
from sensor import Sensor

redis_ok = False
serial_ok = False

# connecting to redis
r = redis.Redis(host='localhost', port=REDIS_PORT, db=0)
try:
    if r.ping():
        print("Connected to Redis!")
        redis_ok = True
except:
    print("Failed to connect to Redis.")

# connecting to serial port
try:
    ser = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1)
    ser.reset_input_buffer()
    print(f"Connected to Arduino on {ARDUINO_PORT}")
    serial_ok = True
except serial.SerialException as e:
    print(f"Error opening serial port {ARDUINO_PORT}, proceeding with simulation mode")

sent_counter = 0

sensor_1 = Sensor(filter_type="NONE")
if serial_ok:
    try:
        while True:
            try:
                if ser.in_waiting > 0:
                    last_sent = 0
                    raw_data = ser.readline().decode('utf-8').strip()
                    print(f"Received: {raw_data}")
                    type_of_data, data = parse_data_one_sensor(raw_data)
                    if type_of_data == "*":
                        sensor_1.add_gravity_recording(data[0], data[1], data[2])
                        sensor_1.calculate_and_set_starting_quaternion()

                        data_to_send_sensor_1 = sensor_1.get_pose(data_type="*")
                    elif type_of_data == "#":
                        timestamp, quaternion_sensor_1, accelerations_sensor_1 = data
                        sensor_1.add_recording(timestamp, quaternion_sensor_1, accelerations_sensor_1)
                        sensor_1.calculate_and_set_state()

                        data_to_send_sensor_1 = sensor_1.get_pose(data_type="#")

                    else:
                        data_to_send_sensor_1 = None

                    data_to_send = {
                        "sensor_1": data_to_send_sensor_1,
                        "sensor_2": None,
                    }

                    r.publish(CHANNEL, json.dumps(data_to_send))

            except serial.SerialException as e:
                pass

    except KeyboardInterrupt:
        print("Exiting program.")

    finally:
        # Close the serial connection
        ser.close()

        print("Serial connection closed.")
else: # questo è gia con due sensori, quando paul è pronto prendi questo codice e mettilo su
    time.sleep(1)
    sensor_1 = Sensor(filter_type="NONE", initial_position=np.array([0, 0, 5]))
    sensor_2 = Sensor(filter_type="NONE", initial_position=np.array([3, 0, 3]))
    SIMULATED_RECORDINGS_G = ["*,0,0,1,1,0,1" for i in range(10)]
    SIMULATED_RECORDINGS_POSES = [f"#,{i},1,0,0,0,0,0,0,1,0,0,0,0,0,0" for i in range(100)]
    SIMULATED_RECORDINGS = SIMULATED_RECORDINGS_G + SIMULATED_RECORDINGS_POSES

    for i in SIMULATED_RECORDINGS:
        print(f"SIMULATED RECORDING: {i}")
        type_of_data, data_sensor_1, data_sensor_2 = parse_data_two_sensors(i)
        if type_of_data == "*":
            sensor_1.add_gravity_recording(data_sensor_1)
            sensor_1.calculate_and_set_starting_quaternion()
            sensor_2.add_gravity_recording(data_sensor_2)
            sensor_2.calculate_and_set_starting_quaternion()

            data_to_send_sensor_1 = sensor_1.get_pose(data_type="*")
            data_to_send_sensor_2 = sensor_2.get_pose(data_type="*")
        elif type_of_data == "#":
            timestamp_1, quaternion_sensor_1, accelerations_sensor_1 = data_sensor_1
            timestamp_2, quaternion_sensor_2, accelerations_sensor_2 = data_sensor_2

            sensor_1.add_recording(timestamp_1, quaternion_sensor_1, accelerations_sensor_1)
            sensor_1.calculate_and_set_state()
            sensor_2.add_recording(timestamp_2, quaternion_sensor_2, accelerations_sensor_2)
            sensor_2.calculate_and_set_state()

            data_to_send_sensor_1 = sensor_1.get_pose(data_type="#")
            data_to_send_sensor_2 = sensor_2.get_pose(data_type="#")
        else:
            data_to_send_sensor_1 = {"data_type": type_of_data}
            data_to_send_sensor_2 = {"data_type": type_of_data}

        data_to_send = {
            "sensor_1" : data_to_send_sensor_1,
            "sensor_2" : None  # data_to_send_sensor_2,
        }
        print("data_to_send:", data_to_send)


        r.publish(CHANNEL, json.dumps(data_to_send))
        time.sleep(PYTHON_SIMULATION_SAMPLING_RATE)
