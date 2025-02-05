import json
import time

import numpy as np
import redis
import serial

from constants import CHANNEL, ARDUINO_PORT, BAUD_RATE, PYTHON_SAMPLING_RATE, REDIS_PORT, \
    PYTHON_SIMULATION_SAMPLING_RATE, QUATERNIONS_TIBIA, POSITIONS
from data_processing_v2 import parse_data_one_sensor
from quat_acc_to_pos import OneSensorRecording

redis_ok = False
serial_ok = False

# connecting to redis
r = redis.Redis(host='localhost', port=REDIS_PORT, db=0)
try:
    if r.ping():
        print("Connected to Redis!")
        redis_ok = True
except:
    print("Failed to connect to Redis, continuing with NO real time plot")

# connecting to serial port
try:
    ser = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1)
    ser.reset_input_buffer()
    print(f"Connected to Arduino on {ARDUINO_PORT}")
    serial_ok = True
except serial.SerialException as e:
    print(f"Error opening serial port {ARDUINO_PORT}, proceeding with simulation mode")

sent_counter = 0
if serial_ok:
    try:
        is_first = True
        while True:
            try:
                if ser.in_waiting > 0:
                    last_sent = 0
                    raw_data = ser.readline().decode('utf-8').strip()
                    timestamp, quaternion_sensor_1, accelerations_sensor_1 = parse_data_one_sensor(raw_data)
                    timestamp = timestamp / 10000
                    if quaternion_sensor_1 is not None and accelerations_sensor_1 is not None:
                        if is_first:
                            RecordingHandler = OneSensorRecording(initial_timestamp=timestamp)
                            is_first = False

                        RecordingHandler.add_pose(timestamp, quaternion_sensor_1, accelerations_sensor_1)
                        RecordingHandler.update()
                        r.publish(CHANNEL, json.dumps({
                            "timestamp": timestamp,
                            "quaternion": quaternion_sensor_1,
                            "position": RecordingHandler.positions[-1]}))

                        sent_counter += 1
                        if sent_counter > 10:
                            print(f"Sent {sent_counter} quaternions")
                            sent_counter = 0
            except serial.SerialException as e:
                pass

    except KeyboardInterrupt:
        print("Exiting program.")

    finally:
        # Close the serial connection
        ser.close()
        print("Serial connection closed.")
else:
    time.sleep(1)
    x = 0
    for i in range(10000):
        tibia_quaternion = QUATERNIONS_TIBIA[i % len(QUATERNIONS_TIBIA)]
        femur_quaternion = QUATERNIONS_TIBIA[len(QUATERNIONS_TIBIA) - 1 - i % len(QUATERNIONS_TIBIA)]

        if redis_ok:
            raw_data = {
                "quaternion": [tibia_quaternion[1], tibia_quaternion[0], tibia_quaternion[2], tibia_quaternion[3]],
                "position": POSITIONS[i % len(POSITIONS)],
            }
            raw_data_dumped = json.dumps(raw_data)
            r.publish(CHANNEL, raw_data_dumped)
            time.sleep(PYTHON_SIMULATION_SAMPLING_RATE)
