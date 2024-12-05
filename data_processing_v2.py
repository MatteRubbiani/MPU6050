
def parse_data(data):
    try:
        timestamp, w, x, y, z, w1, x1, y1, z1 = map(float, data.strip().split(', '))
        return [timestamp, np.asarray([w, x, y, z]), np.asarray([w1, x1, y1, z1])]
    except ValueError:
        print(f"Invalid data format: {data}")
        return [None, None, None]

import numpy as np
from scipy.spatial.transform import Rotation as R

def relative_quaternion(q_previous, q_current):
    # Convert quaternions to scipy Rotation objects
    r_previous = R.from_quat(q_previous)  # [x, y, z, w]
    r_current = R.from_quat(q_current)  # [x, y, z, w]

    # Calculate the relative quaternion
    r_relative = r_previous.inv() * r_current

    # Return the relative quaternion as [x, y, z, w]
    return r_relative.as_quat()


