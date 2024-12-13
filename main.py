import json
import socket
import time

import numpy as np
import redis

from constants import CHANNEL, PYTHON_SAMPLING_RATE, REDIS_PORT, \
    QUATERNIONS_TIBIA, ESP_IP, ESP_PORT, PYTHON_SIMULATION_SAMPLING_RATE
from data_processing_v2 import parse_data
from data_recording import DataSaver

redis_ok = False
wifi_ok = False

# connecting to redis
r = redis.Redis(host='localhost', port=REDIS_PORT, db=0)
try:
    if r.ping():
        print("Connected to Redis!")
        redis_ok = True
except:
    print("Failed to connect to Redis, continuing with NO real time plot")

if wifi_ok:
    # initialize wifi connection, todo: check it
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((ESP_IP, ESP_PORT))
    # start DataSaver
    data_saver = DataSaver(buffer_size=1000)

    try:
        while True:
            data = client.recv(1024)  # Receive data from ESP32
            if data:

                last_tibia_sent = np.asarray([1, 0, 0, 0])
                last_femur_sent = np.asarray([1, 0, 0, 0])

                data = data.decode().strip().split("\n")[0]
                last_sent = 0
                timestamp, quaternion_tibia, quaternion_femur = parse_data(data)
                if quaternion_tibia is not None and quaternion_femur is not None:
                    quaternion_tibia = [quaternion_tibia[0], quaternion_tibia[1], quaternion_tibia[3], quaternion_tibia[2]]
                    quaternion_femur = [quaternion_femur[0], quaternion_femur[1], quaternion_femur[3], quaternion_femur[2]]

                    data_saver.add_data(timestamp, quaternion_tibia, quaternion_femur)
                    if redis_ok:
                        now = time.time()
                        if now > last_sent + PYTHON_SAMPLING_RATE:
                            r.publish(CHANNEL,
                                      json.dumps([timestamp, ] + list(quaternion_tibia) + list(quaternion_femur)))

            time.sleep(0.008)  # Match ESP32 data rate
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        client.close()
else:
    time.sleep(1)
    x = 0
    data_saver = DataSaver(buffer_size=10)
    for i in range(10000):
        tibia_quaternion = QUATERNIONS_TIBIA[i % len(QUATERNIONS_TIBIA)]
        femur_quaternion = QUATERNIONS_TIBIA[len(QUATERNIONS_TIBIA) - 1 - i % len(QUATERNIONS_TIBIA)]
        data_saver.add_data(time.time() * 1000, list(tibia_quaternion), list(femur_quaternion)) # in millisecnds
        if redis_ok:
            raw_data = json.dumps([time.time(), ] + list(tibia_quaternion) + list(femur_quaternion))
            r.publish(CHANNEL, raw_data)
            time.sleep(PYTHON_SIMULATION_SAMPLING_RATE)
        time.sleep(0.008)
