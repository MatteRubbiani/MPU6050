import json

import redis
import serial
import time

from arduino_data_processing import parse_data, qv_mult, quaternions_to_vectors
from constants import CHANNEL, ARDUINO_PORT, BAUD_RATE, PYTHON_SAMPLING_RATE, QUATERNIONS, VECTORS_TIBIA, VECTORS_FEMUR, \
    PYTHON_SIMULATION_SAMPLING_RATE, REDIS_PORT

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

if serial_ok:
    try:
        while True:
            time.sleep(PYTHON_SAMPLING_RATE)
            try:
                if ser.in_waiting > 0:
                    raw_data = ser.readline().decode('utf-8').strip()
                    quaternions = parse_data(raw_data)
                    if quaternions:
                        # print(raw_data)
                        # print(quaternions)
                        tibia_new_vector, femur_new_vector = quaternions_to_vectors(quaternions)
                        if redis_ok:
                            r.publish(CHANNEL, json.dumps(tibia_new_vector + femur_new_vector))
                            # r.rpush("quaternion_list_raw", raw_data)
            except serial.SerialException as e:
                pass

    except KeyboardInterrupt:
        print("Exiting program.")

    finally:
        # Close the serial connection
        ser.close()
        print("Serial connection closed.")
else:
    for i in range(1000000):
        tibia_new_vector = VECTORS_TIBIA[i%len(VECTORS_TIBIA)]
        femur_new_vector = VECTORS_FEMUR[i%len(VECTORS_FEMUR)]
        if redis_ok:
            raw_data = json.dumps(femur_new_vector + tibia_new_vector)
            r.publish(CHANNEL, raw_data)
            r.rpush("quaternion_list_raw", raw_data)
            time.sleep(PYTHON_SIMULATION_SAMPLING_RATE)

