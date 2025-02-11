import json
import numpy as np
from scipy.spatial.transform import Rotation as R


def create_cirular_motion(number_of_steps = 100, acc_modulus = 1, delta_timestamps = 0.1):
    time = 0
    data_list = []
    for i in range(number_of_steps):
        theta_rad = i / number_of_steps * 2 * np.pi
        acc_x = - acc_modulus * np.cos(theta_rad)
        acc_y = - acc_modulus * np.sin(theta_rad)
        acc_z = 0
        data = [time, [0, 0, 0, 1], [acc_x, acc_y, acc_z]]
        data_list.append(data)
        time += delta_timestamps
    return data_list

def create_rotating_circular_motion(number_of_steps = 100, acc_modulus = 1, delta_timestamps = 0.1):
    angle_degrees = 360
    angles = np.linspace(0, np.radians(angle_degrees), number_of_steps)
    quaternions = [R.from_euler('z', angle).as_quat() for angle in angles]
    time = 0
    data_list = []
    for i in range(number_of_steps):
        data = [time, quaternions[i].tolist(), [-acc_modulus, 0, 0]]
        data_list.append(data)
        time += delta_timestamps
    return data_list



def create_linear_acceleration_motion(number_of_steps = 100, acc_modulus = 0.1, delta_timestamps = 0.1):
    time = 0
    data_list = []
    for i in range(number_of_steps):
        acc_x = acc_modulus
        acc_y = 0
        acc_z = 0
        data = [time, [0, 0, 0, 1], [acc_x, acc_y, acc_z]]
        data_list.append(data)
        time += delta_timestamps
    data_list.append([time, [0, 0, 0, 1], [0, 0, 0]])
    time += delta_timestamps
    for i in range(number_of_steps):
        acc_x = - acc_modulus
        acc_y = 0
        acc_z = 0
        data = [time, [0, 0, 0, 1], [acc_x, acc_y, acc_z]]
        data_list.append(data)
        time += delta_timestamps

    return data_list