import numpy as np
from scipy.spatial.transform import Rotation as R


def parse_data(data):
    try:
        timestamp, w, x, y, z, w1, x1, y1, z1 = map(float, data.strip().split(', '))
        return [timestamp, np.asarray([w, x, y, z]), np.asarray([w1, x1, y1, z1])]
    except ValueError:
        print(f"Invalid data format: {data}")
        return [None, None, None]


def parse_data_one_sensor(data):
    try:
        timestamp, q_w, q_x, q_y, q_z, p_x, p_y, p_z = map(float, data.strip().split(', '))
        three_quaternion = (q_x, q_y, q_z, q_w)
        accelerations = (p_x, p_y, p_z)
        return [timestamp, three_quaternion, accelerations]
    except ValueError:
        print(f"Invalid data format: {data}")
        return [None, None, None]

