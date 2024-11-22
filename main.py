import json

import redis
import serial
import time

from arduino_data_processing import parse_data, qv_mult
from constants import CHANNEL, ARDUINO_PORT, BAUD_RATE, PYTHON_SAMPLING_RATE, QUATERNIONS

redis_ok = False
serial_ok = False

# connecting to redis
r = redis.Redis(host='localhost', port=6379, db=0)
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
            if ser.in_waiting > 0:
                raw_data = ser.readline().decode('utf-8').strip()
                # print(raw_data)
                quaternion = parse_data(raw_data)

                if redis_ok:
                    r.publish(CHANNEL, json.dumps(quaternion))
                    r.rpush("quaternion_list_raw", raw_data)

    except KeyboardInterrupt:
        print("Exiting program.")

    finally:
        # Close the serial connection
        ser.close()
        print("Serial connection closed.")
else:
    for i in range(1000000):
        q = QUATERNIONS[i%len(QUATERNIONS)]
        if redis_ok:
            v_new_position = qv_mult(q, (0, 0, 1))
            raw_data = json.dumps(v_new_position)
            r.publish(CHANNEL, raw_data)
            r.rpush("quaternion_list_raw", raw_data)
            time.sleep(0.1)

