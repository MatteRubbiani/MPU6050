import threading
import time

import keyboard
import redis
import csv

from constants import CHANNEL, BUFFER_SIZE, RECORD_FOLDER, REDIS_PORT


def write_buffer_to_file(filename, _buffer):
    with open(filename, "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(_buffer)
    _buffer.clear()

def start_new_recording():
    try:
        r = redis.Redis(host='localhost', port=REDIS_PORT, db=0)
        pubsub = r.pubsub()
        pubsub.subscribe(CHANNEL)
    except redis.ConnectionError:
        print("Could not connect to redis")
        return
    recording_file_name = RECORD_FOLDER + time.strftime("%Y-%m-%d-%H:%M:%S") + ".csv"
    print("starting new recording, recording file is " + recording_file_name)
    buffer = []
    i = 1
    for message in pubsub.listen():
        # Message type 'message' means it is a published message
        if message['type'] == 'message':
            data = message['data'].decode('utf-8').strip("[]").split(",")
            buffer.append(data)
            i += 1
        if stop_event.is_set():
            print("Stopping recording, saving last data...")
            write_buffer_to_file(recording_file_name, buffer)
            return
        elif i >= BUFFER_SIZE:
            write_buffer_to_file(recording_file_name, buffer)
            i = 0



option = input("Enter to start recording, x o quit")
while option != "x":
    print("recording started, enter to stop")
    stop_event = threading.Event()
    background_thread = threading.Thread(target=start_new_recording)
    background_thread.start()
    keyboard.wait("enter")
    option = input()
    stop_event.set()  # Signal the background thread to stop
    background_thread.join()  # Wait for the thread to finish
    print("Recording stopped")
    option = input("Enter to start a new recording, x o quit")