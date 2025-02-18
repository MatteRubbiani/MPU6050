import logging
import time
import redis

from constants import REDIS_PORT
from serial_reader import SerialReader
from simulation.simulate_main_v3 import simulate_main

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def get_r():
    _r = redis.Redis(host='localhost', port=REDIS_PORT, db=0)
    redis_ok = False
    while not redis_ok:
        time.sleep(1)
        try:
            if _r.ping():
                print("✅ Successfully connected to Redis!")
                redis_ok = True
        except redis.ConnectionError as e:
            print(f"❌ Redis connection failed: {e} trying again...")
    return _r

# waits until redis is ready
r = get_r()

mode = input("serial mode? (Y/n): ")
if mode == "n":
    simulate_main(r)
else:
    # todo: controllare g mandato ogni tanto che non resetta i quaternioni e fa casino
    reader = SerialReader(baudrate=115200, r=r)
    reader.start()
    try:
        while True:
            time.sleep(1)  # Keep main thread alive
    except KeyboardInterrupt:
        logging.info("Stopping...")
        reader.stop()

