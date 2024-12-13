import json
import time

import numpy as np
import redis
import serial

# from arduino_data_processing import parse_data, quaternions_to_vectors
from constants import CHANNEL, ARDUINO_PORT, BAUD_RATE, PYTHON_SAMPLING_RATE, REDIS_PORT, \
    PYTHON_SIMULATION_SAMPLING_RATE, QUATERNIONS_TIBIA
from data_processing_v2 import parse_data, relative_quaternion

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
    last_sent_time = time.time()
    last_tibia_sent = np.asarray([1, 0, 0, 0])
    last_femur_sent = np.asarray([1, 0, 0, 0])
    try:
        while True:
            try:
                if ser.in_waiting > 0:
                    last_sent = 0
                    raw_data = ser.readline().decode('utf-8').strip()
                    timestamp, quaternion_tibia, quaternion_femur = parse_data(raw_data)
                    if quaternion_tibia is not None and quaternion_femur is not None:
                        # forse sarebbe meglio registrare i dati qua? evitiamo lag e python sampling rate??
                        # send data with sampling rate
                        if redis_ok:
                            now = time.time()
                            if now > last_sent + PYTHON_SAMPLING_RATE:
                                q_rel_tibia = relative_quaternion(last_tibia_sent, quaternion_tibia)
                                q_rel_femur = relative_quaternion(last_femur_sent, quaternion_femur)
                                # print(q_rel_tibia, q_rel_femur)

                                r.publish(CHANNEL, json.dumps([timestamp, ] + list(q_rel_tibia) + list(q_rel_femur)))
                                last_sent = now
                                last_tibia_sent = quaternion_tibia
                                last_femur_sent = quaternion_femur
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
            raw_data = json.dumps([0, ] + tibia_quaternion + femur_quaternion)
            r.publish(CHANNEL, raw_data)
            r.rpush("quaternion_list_raw", raw_data)
            time.sleep(PYTHON_SIMULATION_SAMPLING_RATE)
