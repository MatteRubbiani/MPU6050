import json
import math

import numpy as np
from scipy.spatial.transform import Rotation as R

from constants import FILTERS


class Sensor:
    def __init__(self, initial_quaternion=np.array((0, 0, 0, 1)), initial_position=np.array((0, 0, 0)), filter_type="NONE"):
        self.filter_type = FILTERS[filter_type]
        self.last_delta_timestamp = None
        self.initial_quaternion = initial_quaternion
        self.initial_position = initial_position

        self.timestamps = []
        self.quaternions = []
        self.accelerations = []
        self.real_world_accelerations = []

        self.real_world_velocities = []
        self.real_world_positions = []
        self.records_counter = 0

        self.starting_g = np.array([0, 1, 0])
        self.g_recordings = []


    def add_gravity_recording(self, gx, gy, gz):
        self.g_recordings.append(np.array([gx, gy, gz]))

    def calculate_and_set_starting_quaternion(self):
        mean_g = np.mean(self.g_recordings, axis=0)
        quat = quaternion_from_recorded_g_giac(mean_g)
        self.initial_quaternion = np.array(quat)

    def add_recording(self, timestamp, quaternion, acceleration):
        self.timestamps.append(timestamp)
        self.quaternions.append(np.array(quaternion))
        self.accelerations.append(np.array(acceleration))
        self.__calculate_and_set_real_world_acceleration(quaternion, acceleration)
        #todo: attenzione, il quaternione che applico all'accelerazione NON tiene conto del quaternione iniale. Le posizioni che scono sono quindi relative agli assi del sensore. Prima di applicarle vanno ruotate del quaternione inziiale!!!

        self.records_counter += 1

    def calculate_and_set_state(self):
        if self.records_counter == 0:
            print("No recording")
            return
        elif self.records_counter == 1:
            # self.real_world_velocities.append(np.zeros(3))
            self.real_world_velocities.append(np.array([0, 0, 0]))
            self.real_world_positions.append(np.zeros(3))
        else:
            self.last_delta_timestamp = self.timestamps[-1] - self.timestamps[-2]
            self.__calculate_and_set_real_world_velocity()
            self.__calculate_and_set_real_world_position()

    def get_pose(self, data_type="#", get_acceleration=False, dumped=False):
        pose_undumped = {
            "data_type": data_type
        }
        if data_type == "#":
            pose_undumped["timestamp"] = self.timestamps[-1]
            pose_undumped["quaternion"] = self.quaternions[-1].tolist()
            pose_undumped["position"] = self.real_world_positions[-1].tolist()
            if get_acceleration:
                pose_undumped["acceleration"] = self.real_world_accelerations[-1].tolist()
        elif data_type == "*":
            pose_undumped["q"] = self.initial_quaternion.tolist()
            pose_undumped["p"] = self.initial_position.tolist()

        data_to_publish = json.dumps(pose_undumped) if dumped else pose_undumped
        return data_to_publish

    def __calculate_and_set_real_world_acceleration(self, quaternion, acceleration):
        self.real_world_accelerations.append(R.from_quat(quaternion).apply(acceleration))

    def __calculate_and_set_real_world_velocity(self):
        last_r_w_acceleration = self.real_world_accelerations[-1]
        last_r_w_velocity = self.real_world_velocities[-1]
        total_r_w_velocity = last_r_w_velocity + (last_r_w_acceleration * self.last_delta_timestamp)
        if self.filter_type == 0:
            self.real_world_velocities.append(total_r_w_velocity)
        elif self.filter_type == 1:
            delta_acceleration = self.real_world_accelerations[-1] - self.real_world_accelerations[-2]
            if np.linalg.norm(delta_acceleration) > 0.3:
                self.real_world_velocities.append(1*total_r_w_velocity)
            else:
                self.real_world_velocities.append(np.zeros(3))

        else:
            pass


    def __calculate_and_set_real_world_position(self):
        last_r_w_velocity = self.real_world_velocities[-1]
        last_r_w_position = self.real_world_positions[-1]
        total_r_w_position = last_r_w_position + last_r_w_velocity * self.last_delta_timestamp
        self.real_world_positions.append(total_r_w_position)



def quaternion_between_vectors(v1, v2):
    if np.linalg.norm(v1) != 0:
        v1 = v1 / np.linalg.norm(v1)  # Normalize v1
    if  np.linalg.norm(v2) != 0:
        v2 = v2 / np.linalg.norm(v2)  # Normalize v2

    dot_product = np.dot(v1, v2)  # Compute dot product
    if np.isclose(dot_product, 1.0):
        return np.array([1, 0, 0, 0])  # No rotation needed (identity quaternion)
    if np.isclose(dot_product, -1.0):
        return np.array([0, 1, 0, 0])  # 180-degree rotation (arbitrary axis)

    axis = np.cross(v1, v2)  # Compute rotation axis
    axis = axis / np.linalg.norm(axis)  # Normalize axis
    angle = np.arccos(dot_product)  # Compute angle in radians

    q_w = np.cos(angle / 2)
    q_xyz = axis * np.sin(angle / 2)

    return np.concatenate((q_xyz, [q_w]))  # Quaternion (w, x, y, z)


def euler_to_quaternion(theta_x, theta_y, theta_z):
    """
    Converte angoli di Eulero (theta_x, theta_y, theta_z) in un quaternione (w, x, y, z).

    Gli angoli devono essere forniti in **radiani**.
    L'ordine di rotazione è **X (roll) → Y (pitch) → Z (yaw)**.
    """
    cx = np.cos(theta_x / 2)
    sx = np.sin(theta_x / 2)
    cy = np.cos(theta_y / 2)
    sy = np.sin(theta_y / 2)
    cz = np.cos(theta_z / 2)
    sz = np.sin(theta_z / 2)

    w = cz * cy * cx + sz * sy * sx
    x = sx * cy * cz - cx * sy * sz
    y = cx * sy * cz + sx * cy * sz
    z = cx * cy * sz - sx * sy * cz

    return (x, y, z, w)


def quaternions_from_recorded_g(recorded_g): # assumes g alligned with y axis as basis
    normalized_recorded_g = recorded_g / np.linalg.norm(recorded_g)
    ax = normalized_recorded_g[0]
    ay = normalized_recorded_g[1]
    az = normalized_recorded_g[2]


    if abs(ay) < 0.3 and abs(az) < 0.3: # indeterminato, assumiamo = 0
        theta_x = 0
    else:
        theta_x = np.atan(- az / ay)

    if ay < 0:
        theta_x = theta_x + np.pi


    if abs(ax) < 0.3 and abs(ay) < 0.3: # indeterminato, assumiamo = 0
        theta_z = 0
    else:
        theta_z = np.atan(ax / ay)

    if ay < 0:
        theta_z = theta_z + np.pi # se sono nel 23 quadrante

    print(theta_x, theta_z)
    quat = euler_to_quaternion(theta_x, 0, theta_z)
    quat = np.array(quat)
    quat = quat / np.linalg.norm(quat)
    return quat


def axis_angle_to_quaternion(axis, theta):
    """Convert an axis-angle representation to a quaternion.

    Parameters:
    axis (tuple): A 3-element tuple representing the unit axis (x, y, z).
    theta (float): Rotation angle in radians.

    Returns:
    tuple: A 4-element tuple representing the quaternion (w, x, y, z).
    """
    x, y, z = axis
    half_theta = theta / 2
    w = np.cos(half_theta)
    sin_half_theta = np.sin(half_theta)

    return np.array((x * sin_half_theta, y * sin_half_theta, z * sin_half_theta, w))


def quaternion_from_recorded_g_giac(recorded_g):
    normalized_recorded_g = recorded_g / np.linalg.norm(recorded_g)
    a = normalized_recorded_g[0]
    b = normalized_recorded_g[1]
    c = normalized_recorded_g[2]

    cos_theta = b
    sin_theta = - math.sqrt(a * a + c * c)

    theta = math.atan2(sin_theta, cos_theta)
    axis = (c, 0, -a)
    axis = axis / np.linalg.norm(axis)

    # if recorded_g = 0, -1, 0 --> undefined axis => set it to (1, 0, 0)
    if np.linalg.norm(axis) == 0:
        axis = np.array([1, 0, 0])
    # aggiungere anche la condizione 0, 1, 0 -> ora da axis = Nan, Nan,Nan
    print("theta: ", theta, "axis: ", axis)

    """quat = axis_angle_to_quaternion(axis, theta)
    print("theta: ", theta, "axis: ", axis)
    return quat"""
    return R.from_rotvec(theta * np.array(axis)).as_quat()





if __name__ == "__main__":
    print(quaternion_from_recorded_g_giac(np.array([0, 0, 1])))