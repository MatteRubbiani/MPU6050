import math
from datetime import time

import numpy as np
from scipy.spatial.transform import Rotation as R

class OneSensorRecording:
    def __init__(self, initial_quaternion_sensor_1=(0, 0, 0, 1), initial_position_sensor_1=(0, 0, 0, 1), initial_timestamp=None):
        self.initial_quaternion_sensor_1 = initial_quaternion_sensor_1
        self.initial_position_sensor_1 = initial_position_sensor_1
        self.initial_timestamp = initial_timestamp if initial_timestamp else time.time()
        self.timestamps = []        # facciamoli parteire da 0
        self.quaternions = []       # partono da 0, 0, 0, 1 poi ruoto initial quaternion
        self.accelerations = []     # partono da 0
        self.velocities = []        # partono da 0
        self.positions = []         # partono da 0 poi sommo a initial position se serve
        self.__fill_starting_poses()

    def __fill_starting_poses(self):
        self.timestamps.append(0)
        self.quaternions.append([0, 0, 0, 1])
        self.accelerations.append([0, 0, 0])
        self.velocities.append([0, 0, 0])
        self.positions.append([0, 0, 0])

    def __get_real_world_accelerations(self, quat, acc):
        acc = np.array(acc)
        quat = np.array(quat)

        # Convert local accelerations to global frame
        global_acceleration = list(
            R.from_quat(quat).apply(acc)
        )
        return global_acceleration

    def __filter_desperation(self, acc):
        if math.sqrt(sum(x**2 for x in acc)) < 1:
            return [0, 0, 0]
        return acc

    def add_pose(self, timestamp, quaternion, acceleration):
        self.timestamps.append(timestamp)
        self.quaternions.append(quaternion)
        self.accelerations.append(self.__filter_desperation(self.__get_real_world_accelerations(quaternion, acceleration)))

    def update(self):
        delta_timestamp = self.timestamps[-1] - self.timestamps[-2]
        delta_velocity = [self.accelerations[-1][i]  * delta_timestamp for i in range(3)]
        last_velocities = self.velocities[-1]
        if sum(self.accelerations[-1]) != 0:
            new_velocities = [last_velocities[i] + delta_velocity[i] for i in range(3)]
        else:
            new_velocities = [0, 0, 0]
        delta_position = [last_velocities[i] * delta_timestamp for i in range(3)]
        self.velocities.append(new_velocities)
        self.positions.append([self.positions[-1][i] + delta_position[i] for i in range(3)])

        self.velocities.append([new_velocities[0], new_velocities[1], 0])




def integrate_acceleration(accelerations, quaternions, timestamps):
    """
    Integrates acceleration twice to get position, considering orientation.

    Parameters:
    - accelerations: (N, 3) array of accelerations in local frame
    - quaternions: (N, 4) array of quaternions [x, y, z, w]
    - timestamps: (N,) array of timestamps

    Returns:
    - positions: (N, 3) array of global positions
    """
    accelerations = np.array(accelerations)
    quaternions = np.array(quaternions)
    timestamps = np.array(timestamps)

    # Convert local accelerations to global frame
    global_accelerations = np.array([
        R.from_quat(q).apply(a) for q, a in zip(quaternions, accelerations)
    ])

    # Compute time differences
    dt = np.diff(timestamps, prepend=timestamps[0])

    # Integrate acceleration to get velocity
    velocities = np.zeros_like(global_accelerations)
    for i in range(1, len(velocities)):
        velocities[i] = velocities[i - 1] + global_accelerations[i - 1] * dt[i]

    # Integrate velocity to get position
    positions = np.zeros_like(global_accelerations)
    for i in range(1, len(positions)):
        positions[i] = positions[i - 1] + velocities[i - 1] * dt[i]

    return positions

