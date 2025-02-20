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

    def add_gravity_recording(self, g):
        self.g_recordings.append(np.array(g))

    def calculate_and_set_starting_quaternion(self):
        mean_g = np.mean(self.g_recordings, axis=0)
        quat = quaternion_from_recorded_g_giac(mean_g)
        self.initial_quaternion = np.array(quat)

    def add_recording(self, timestamp, quaternion, acceleration):
        self.timestamps.append(timestamp)
        self.quaternions.append(np.array(quaternion))
        self.accelerations.append(np.array(acceleration))
        self.__calculate_and_set_real_world_acceleration(quaternion, acceleration)
        #todo: attenzione, il quaternione che applico all'accelerazione NON tiene conto del quaternione iniale. Le posizioni che escono sono quindi relative agli assi del sensore. Prima di applicarle vanno ruotate del quaternione inziiale!!!

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

    def get_pose(self, data_type="#", get_acceleration=False, dumped=False, fixed_position = True, ):
        # a breve non si userà più
        pose_undumped = {
            "data_type": data_type
        }
        if data_type == "#":
            # todo: sistemare sensore, standardizzare un po' :-)
            if len(self.timestamps) == 0:
                return None

            pose_undumped["timestamp"] = self.timestamps[-1]
            pose_undumped["quaternion"] = self.quaternions[-1].tolist()
            # todo: calculate total quaternion (facciamo sparire initial quaternion da three.js)
            pose_undumped["position"] = [0, 0, 0] if fixed_position else self.real_world_positions[-1].tolist()
            if get_acceleration:
                pose_undumped["acceleration"] = self.real_world_accelerations[-1].tolist()
        elif data_type == "*":
            pose_undumped["q"] = self.initial_quaternion.tolist()
            pose_undumped["p"] = self.initial_position.tolist()

        data_to_publish = json.dumps(pose_undumped) if dumped else pose_undumped
        return data_to_publish

    def get_initial_properties(self):
        return {
            "initial_quaternion": self.initial_quaternion.tolist(),
            "initial_position": self.initial_position.tolist()
        }

    def get_current_properties(self, absolute=True):
        if len(self.timestamps) == 0:
            return None

        current_relative_quaternion = self.quaternions[-1].tolist()
        current_relative_position = self.real_world_positions[-1].tolist() # ancora da ruotare del quatenione iniziale, per ora ce ne sbattiamo
        absolute_quaternion = calculate_absolute_quaternion(current_relative_quaternion, self.initial_quaternion)
        print("absolute_quaternion", absolute_quaternion, "initial_quaternion", self.initial_quaternion)
        return {
            "current_quaternion": absolute_quaternion.tolist(),
            "current_position": [0, 0, 0],
            "current_acceleration": [0, 0, 0]
        }

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



def quaternion_from_recorded_g_giac(recorded_g):
    # if g = (0, 1, 0) --> axis undefined
    if np.array_equal(recorded_g, np.array([0, 1, 0])):
        theta = 0
        axis = np.array([1, 0, 0])
    # if g = (0, -1, 0) --> axis undefined
    elif np.array_equal(recorded_g, np.array([0, -1, 0])):
        theta = np.pi
        axis = np.array([1, 0, 0])
    else:
        normalized_recorded_g = recorded_g / np.linalg.norm(recorded_g)
        a = normalized_recorded_g[0]
        b = normalized_recorded_g[1]
        c = normalized_recorded_g[2]

        cos_theta = b
        sin_theta = - math.sqrt(a * a + c * c)

        theta = math.atan2(sin_theta, cos_theta)
        axis = (c, 0, -a)
        axis = axis / np.linalg.norm(axis)

    return R.from_rotvec(theta * np.array(axis)).as_quat()


def calculate_absolute_quaternion(q_rel_array, initial_quaternion):
    # [x, y, z, w] fo scipy
    q_r = R.from_quat(q_rel_array).as_quat()  # Ensure normalized
    q_init = R.from_quat(initial_quaternion).as_quat()

    # Compute q_delta_real_world = InitialQuaternionToUse * q_r
    q_delta_real_world = (R.from_quat(q_init) * R.from_quat(q_r)).as_quat()
    #todo: boh andrà bene?
    print("q_delta_real_world", q_delta_real_world)

    # Compute q_real_world_total = q_delta_real_world * InitialQuaternionToUse
    q_real_world_total = (R.from_quat(q_delta_real_world) * R.from_quat(q_init)).as_quat()

    # Update the sensor object's quaternion (assuming it stores as a NumPy array)

    return q_delta_real_world  # Also returns NumPy array

if __name__ == "__main__":
    print(calculate_absolute_quaternion(np.array([0, 0, -1, 1]), np.array([0, 0, 1, 1])))